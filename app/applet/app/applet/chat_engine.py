import os
import sys
import torch
import torch.nn.functional as F
import random
from typing import Optional, List, Dict, Generator, Tuple

sys.path.insert(0, '/app/applet/nexa-model')
sys.path.insert(0, '/app/applet')
sys.path.insert(0, '/app/applet/app/applet')

from model.config import NexaConfig
from model.transformer import NexaTransformer
from training.checkpoint import load_checkpoint
from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS

class TokenStreamer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.tokens = []
        self.last_decoded_text = ""

    def process_token(self, token_id: int) -> Tuple[str, str]:
        self.tokens.append(token_id)
        current_text = self.tokenizer.decode(self.tokens)
        if current_text.startswith(self.last_decoded_text):
            chunk = current_text[len(self.last_decoded_text):]
        else:
            chunk = current_text
        self.last_decoded_text = current_text
        return chunk, current_text

class ChatEngine:
    def __init__(
        self,
        checkpoint_path: str = '/app/applet/checkpoints/model.pt',
        vocab_path: str = '/app/applet/nexa-model/tokenizer/bpe_vocab.json',
        merges_path: str = '/app/applet/nexa-model/tokenizer/bpe_merges.txt',
        device: Optional[str] = None
    ):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        try:
            self.tokenizer = NexaBPETokenizer()
            if os.path.exists(vocab_path) and os.path.exists(merges_path):
                self.tokenizer.load(vocab_path, merges_path)
            elif os.path.exists('/app/applet/tokenizer/bpe_vocab.json'):
                self.tokenizer.load('/app/applet/tokenizer/bpe_vocab.json', '/app/applet/tokenizer/bpe_merges.txt')
            else:
                print("Warning: Tokenizer files not found, using default special tokens.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BPE Tokenizer: {e}")

        self.eos_token_id = DEFAULT_SPECIAL_TOKENS.get('<EOS>', 2)
        self.bos_token_id = DEFAULT_SPECIAL_TOKENS.get('<BOS>', 1)
        self.pad_token_id = DEFAULT_SPECIAL_TOKENS.get('<PAD>', 0)

        self.config = NexaConfig(
            vocab_size=8000,
            max_seq_len=256,
            d_model=384,
            n_layers=6,
            n_heads=6,
            d_ff=1536,
            dropout=0.1,
            norm_eps=1e-5,
            weight_tying=True,
            bias=False
        )

        try:
            self.model = NexaTransformer(self.config).to(self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize NexaTransformer model: {e}")

        ckpt_candidates = [
            checkpoint_path,
            '/app/applet/checkpoints/model.pt',
            '/app/applet/checkpoints_phase4e/latest.ckpt',
            '/app/applet/checkpoints_phase4e/best.ckpt'
        ]

        loaded_success = False
        last_err = None
        loaded_path = None

        for cp in ckpt_candidates:
            if cp and os.path.exists(cp) and os.path.getsize(cp) > 100000:
                try:
                    load_checkpoint(cp, self.model)
                    loaded_success = True
                    loaded_path = cp
                    print(f"Successfully loaded model checkpoint from {cp}")
                    break
                except Exception as e:
                    last_err = e

        if not loaded_success:
            raise RuntimeError(
                f"CRITICAL: No valid trained checkpoint found in candidates {ckpt_candidates}. "
                f"Refusing to perform inference with un-trained / randomly initialized weights. "
                f"Last error: {last_err}"
            )

        self.loaded_checkpoint_path = loaded_path
        self.model.eval()

    def format_prompt(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        previous_messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        if not user_prompt or not isinstance(user_prompt, str):
            user_prompt = ""

        formatted = ""
        if system_prompt:
            formatted += f"<NEXA_SYSTEM> {system_prompt.strip()}\n"

        if previous_messages:
            for msg in previous_messages:
                role = msg.get("role", "user").lower()
                content = msg.get("content", "").strip()
                if role == "system":
                    formatted += f"<NEXA_SYSTEM> {content}\n"
                elif role == "user":
                    formatted += f"<NEXA_USER> {content}\n"
                elif role == "assistant":
                    formatted += f"<NEXA_ASSISTANT> {content}\n"

        formatted += f"<NEXA_USER> {user_prompt.strip()}\n<NEXA_ASSISTANT>"
        return formatted

    def _sample_token(
        self,
        logits: torch.Tensor,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        generated_ids: Optional[List[int]] = None
    ) -> int:
        logits = logits[0, -1, :]

        if repetition_penalty != 1.0 and generated_ids:
            for tid in set(generated_ids):
                if 0 <= tid < logits.size(0):
                    if logits[tid] < 0:
                        logits[tid] *= repetition_penalty
                    else:
                        logits[tid] /= repetition_penalty

        if temperature < 1e-5:
            return int(torch.argmax(logits).item())

        logits = logits / max(temperature, 1e-5)

        if top_k > 0 and top_k < logits.size(0):
            values, _ = torch.topk(logits, top_k)
            min_top = values[-1]
            logits = torch.where(logits < min_top, torch.tensor(float('-inf'), device=logits.device), logits)

        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = False

            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            logits[indices_to_remove] = float('-inf')

        probs = F.softmax(logits, dim=-1)

        if torch.isnan(probs).any() or torch.isinf(probs).any() or probs.sum() <= 0:
            return int(torch.argmax(logits).item())

        next_token = torch.multinomial(probs, num_samples=1).item()
        return int(next_token)

    def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        previous_messages: Optional[List[Dict[str, str]]] = None,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        seed: Optional[int] = None
    ) -> str:
        if seed is not None:
            torch.manual_seed(seed)
            random.seed(seed)

        prompt_str = self.format_prompt(user_prompt, system_prompt, previous_messages)
        input_ids = self.tokenizer.encode(prompt_str)
        if not input_ids:
            input_ids = [self.bos_token_id]

        max_seq_len = self.config.max_seq_len
        if len(input_ids) >= max_seq_len:
            input_ids = input_ids[-(max_seq_len - 10):]

        generated_ids = []
        current_ids = list(input_ids)
        self.model.eval()

        with torch.no_grad():
            for _ in range(max_new_tokens):
                ctx = current_ids[-max_seq_len:]
                input_tensor = torch.tensor([ctx], dtype=torch.long, device=self.device)

                logits, _ = self.model(input_tensor, None)
                if torch.isnan(logits).any():
                    break

                next_token = self._sample_token(
                    logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_ids=generated_ids
                )

                if next_token == self.eos_token_id or next_token < 0 or next_token >= self.config.vocab_size:
                    break

                generated_ids.append(next_token)
                current_ids.append(next_token)

        response_text = self.tokenizer.decode(generated_ids)
        return response_text

    def stream_generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        previous_messages: Optional[List[Dict[str, str]]] = None,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        seed: Optional[int] = None
    ) -> Generator[Tuple[str, str], None, None]:
        if seed is not None:
            torch.manual_seed(seed)
            random.seed(seed)

        prompt_str = self.format_prompt(user_prompt, system_prompt, previous_messages)
        input_ids = self.tokenizer.encode(prompt_str)
        if not input_ids:
            input_ids = [self.bos_token_id]

        max_seq_len = self.config.max_seq_len
        if len(input_ids) >= max_seq_len:
            input_ids = input_ids[-(max_seq_len - 10):]

        generated_ids = []
        current_ids = list(input_ids)
        streamer = TokenStreamer(self.tokenizer)

        self.model.eval()
        with torch.no_grad():
            for _ in range(max_new_tokens):
                ctx = current_ids[-max_seq_len:]
                input_tensor = torch.tensor([ctx], dtype=torch.long, device=self.device)

                logits, _ = self.model(input_tensor, None)
                if torch.isnan(logits).any():
                    break

                next_token = self._sample_token(
                    logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_ids=generated_ids
                )

                if next_token == self.eos_token_id or next_token < 0 or next_token >= self.config.vocab_size:
                    break

                generated_ids.append(next_token)
                current_ids.append(next_token)

                chunk, full = streamer.process_token(next_token)
                yield chunk, full
