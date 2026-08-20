from typing import List, Optional
import torch
import torch.nn.functional as F
from .interfaces import GenerationConfig, GenerationRequest, GenerationResult, InferenceEngine
from backend.nexa.inference.sampler import top_k_top_p_filtering

class NexaInferenceEngine(InferenceEngine):
    def __init__(self, model, tokenizer, device: str = 'cpu', pad_token_id: int = 0, eos_token_id: int = 6):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.pad_token_id = pad_token_id
        self.eos_token_id = eos_token_id

    def generate(self, request: GenerationRequest) -> GenerationResult:
        results = self.generate_batch([request])
        return results[0]

    @torch.no_grad()
    def generate_batch(self, requests: List[GenerationRequest]) -> List[GenerationResult]:
        if not isinstance(requests, list):
            raise TypeError("requests must be a list of GenerationRequest")
        if len(requests) == 0:
            return []

        B = len(requests)
        raw_encoded = []
        configs = []
        for req in requests:
            if not isinstance(req, GenerationRequest):
                raise TypeError("Each item in requests must be a GenerationRequest")
            raw_encoded.append(self.tokenizer.encode(req.prompt))
            configs.append(req.config or GenerationConfig())

        max_prompt_len = max(len(toks) for toks in raw_encoded)
        max_new_tokens = max(cfg.max_new_tokens for cfg in configs)
        max_seq_len = getattr(self.model.config, 'max_seq_len', 256)

        # Build left-padded input tensor [B, max_prompt_len]
        padded_prompts = []
        for toks in raw_encoded:
            pad_count = max_prompt_len - len(toks)
            padded_prompts.append([self.pad_token_id] * pad_count + toks)

        input_tensor = torch.tensor(padded_prompts, dtype=torch.long, device=self.device)

        generated_token_ids = [[] for _ in range(B)]
        finished = [False] * B
        finish_reasons = ["length"] * B

        self.model.eval()

        for step in range(max_new_tokens):
            # Truncate context to last max_seq_len tokens
            curr_input = input_tensor[:, -max_seq_len:]
            T = curr_input.size(1)

            # Build attention mask for pad tokens
            pad_mask = (curr_input != self.pad_token_id).long()
            causal_mask = torch.tril(torch.ones((T, T), device=self.device, dtype=torch.bool)).view(1, 1, T, T)
            key_mask = pad_mask.view(B, 1, 1, T)
            combined_mask = causal_mask & (key_mask == 1)

            logits, _ = self.model(curr_input, attention_mask=combined_mask)
            next_logits = logits[:, -1, :] # [B, vocab_size]

            next_tokens_step = []
            for b in range(B):
                cfg = configs[b]
                if finished[b] or len(generated_token_ids[b]) >= cfg.max_new_tokens:
                    if not finished[b]:
                        finished[b] = True
                        finish_reasons[b] = "length"
                    next_tokens_step.append(self.pad_token_id)
                    continue

                row_logits = next_logits[b:b+1, :].clone()
                if cfg.repetition_penalty != 1.0:
                    for tid in set(raw_encoded[b] + generated_token_ids[b]):
                        if tid < row_logits.size(-1):
                            row_logits[0, tid] /= cfg.repetition_penalty

                if not cfg.do_sample or cfg.temperature < 1e-5:
                    chosen_tok = int(torch.argmax(row_logits, dim=-1).item())
                else:
                    filtered = top_k_top_p_filtering(row_logits / cfg.temperature, top_k=cfg.top_k, top_p=cfg.top_p)
                    probs = F.softmax(filtered, dim=-1)
                    chosen_tok = int(torch.multinomial(probs, num_samples=1).item())

                if chosen_tok == self.eos_token_id:
                    finished[b] = True
                    finish_reasons[b] = "stop"
                    next_tokens_step.append(self.pad_token_id)
                else:
                    generated_token_ids[b].append(chosen_tok)
                    next_tokens_step.append(chosen_tok)
                    if len(generated_token_ids[b]) >= cfg.max_new_tokens:
                        finished[b] = True
                        finish_reasons[b] = "length"

            step_tensor = torch.tensor(next_tokens_step, dtype=torch.long, device=self.device).view(B, 1)
            input_tensor = torch.cat([input_tensor, step_tensor], dim=-1)

            if all(finished):
                break

        results = []
        for b in range(B):
            text = self.tokenizer.decode(generated_token_ids[b])
            results.append(GenerationResult(
                text=text,
                tokens_generated=len(generated_token_ids[b]),
                finish_reason=finish_reasons[b]
            ))

        return results
