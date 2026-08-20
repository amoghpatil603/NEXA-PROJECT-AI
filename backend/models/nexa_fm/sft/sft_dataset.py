import json
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

class SFTDataset:
    """
    Dataset loader for Supervised Fine-Tuning (SFT).
    Implements loss masking (prompt tokens set to -100 in labels so loss is assistant-only).
    """
    def __init__(
        self,
        file_path: str,
        tokenizer: Optional[Any] = None,
        max_seq_len: int = 2048,
        pad_token_id: int = 0
    ):
        self.file_path = Path(file_path)
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.pad_token_id = pad_token_id
        self.records: List[Dict[str, str]] = []
        self._load()

    def _load(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"SFT dataset file not found: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                prompt = data.get("prompt") or data.get("instruction", "")
                response = data.get("response") or data.get("output", "")
                if prompt and response:
                    self.records.append({"prompt": prompt, "response": response})

    def __len__(self):
        return len(self.records)

    def format_prompt_response(self, prompt: str, response: str) -> Dict[str, str]:
        formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        formatted_response = f"{response}<|im_end|>"
        return {"prompt": formatted_prompt, "response": formatted_response, "full_text": formatted_prompt + formatted_response}

    def process_item_with_masking(self, prompt: str, response: str, encode_fn) -> Dict[str, torch.Tensor]:
        formatted = self.format_prompt_response(prompt, response)
        prompt_tokens = encode_fn(formatted["prompt"])
        response_tokens = encode_fn(formatted["response"])
        
        full_tokens = prompt_tokens + response_tokens
        if len(full_tokens) > self.max_seq_len:
            full_tokens = full_tokens[:self.max_seq_len]

        # Labels: -100 for prompt tokens (loss ignored), actual token IDs for assistant response
        prompt_len = min(len(prompt_tokens), self.max_seq_len)
        labels = [-100] * prompt_len + full_tokens[prompt_len:]

        return {
            "input_ids": torch.tensor(full_tokens, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long)
        }
