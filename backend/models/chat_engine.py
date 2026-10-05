import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Generator, Tuple, Any

import torch
import torch.nn.functional as F

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.training.checkpoint import load_checkpoint
from backend.models.tokenizer.bpe_tokenizer import DEFAULT_SPECIAL_TOKENS
from backend.models.tokenizer.incremental_bpe import IncrementalBPETokenizer

ROOT = Path(__file__).resolve().parents[2]

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
        checkpoint_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
        merges_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        try:
            tok_candidates = [
                vocab_path,
                str(ROOT / "backend/models/tokenizer/production/tokenizer.json"),
                str(ROOT / "backend/tokenizer_v1/tokenizer.json")
            ]
            loaded_tok = False
            for p in tok_candidates:
                if os.path.exists(p):
                    self.tokenizer = IncrementalBPETokenizer.load(p)
                    loaded_tok = True
                    print(f"Successfully loaded tokenizer from {p}")
                    break
            if not loaded_tok:
                raise RuntimeError("Canonical NEXA tokenizer not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BPE Tokenizer: {e}")

        self.eos_token_id = DEFAULT_SPECIAL_TOKENS.get('<EOS>', 2)
        self.bos_token_id = DEFAULT_SPECIAL_TOKENS.get('<BOS>', 1)
        self.pad_token_id = DEFAULT_SPECIAL_TOKENS.get('<PAD>', 0)

        checkpoint = self._find_checkpoint(checkpoint_path)
        self.config = self._load_checkpoint_config(checkpoint)

        try:
            self.model = NexaTransformer(self.config).to(self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize NexaTransformer model: {e}")

        try:
            load_checkpoint(checkpoint, self.model, device=self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to load trained NEXA checkpoint {checkpoint}: {e}") from e

        self.loaded_checkpoint_path = str(checkpoint)
        self.model.eval()

    @staticmethod
    def _load_checkpoint_config(checkpoint: Path) -> NexaConfig:
        try:
            state = torch.load(checkpoint, map_location="cpu", weights_only=False)
            cfg = state.get("config") if isinstance(state, dict) else None
            if isinstance(cfg, NexaConfig):
                return cfg
            if isinstance(cfg, dict):
                allowed = {k: v for k, v in cfg.items() if k in NexaConfig.__dataclass_fields__}
                return NexaConfig(**allowed)
        except Exception:
            pass
        return NexaConfig.tiny()

    @staticmethod
    def _find_checkpoint(explicit: Optional[str]) -> Path:
        candidates = []
        if explicit:
            candidates.append(Path(explicit))
        if os.getenv("NEXA_CHECKPOINT"):
            candidates.append(Path(os.environ["NEXA_CHECKPOINT"]))
        candidates.extend([
            ROOT / "checkpoints" / "model.pt",
            ROOT / "checkpoints" / "nexa_final.pt",
            ROOT / "checkpoints_dpo" / "best.ckpt",
            ROOT / "checkpoints_sft" / "best.ckpt",
            ROOT / "checkpoints_phase4e" / "best.ckpt",
            ROOT / "checkpoints_phase4e" / "latest.ckpt",
        ])
        for path in candidates:
            path = path.expanduser()
            if path.is_file() and path.stat().st_size > 100_000:
                return path
        raise RuntimeError("No trained NEXA checkpoint found. Set NEXA_CHECKPOINT to a valid .ckpt/.pt file.")

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
        logits: 'Any',
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
