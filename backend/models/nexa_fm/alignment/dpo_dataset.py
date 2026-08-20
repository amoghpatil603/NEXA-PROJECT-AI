import json
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

class DPODataset:
    """
    Dataset loader for Direct Preference Optimization (DPO).
    Parses pairwise JSONL files with prompt, chosen, and rejected responses.
    """
    def __init__(self, file_path: str, max_seq_len: int = 2048):
        self.file_path = Path(file_path)
        self.max_seq_len = max_seq_len
        self.pairs: List[Dict[str, str]] = []
        self._load()

    def _load(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"DPO dataset file not found: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                prompt = data.get("prompt", "")
                chosen = data.get("chosen", "")
                rejected = data.get("rejected", "")
                if prompt and chosen and rejected:
                    self.pairs.append({"prompt": prompt, "chosen": chosen, "rejected": rejected})

    def __len__(self):
        return len(self.pairs)

    def format_pair(self, item: Dict[str, str], encode_fn) -> Dict[str, torch.Tensor]:
        prompt_text = f"<|im_start|>user\n{item['prompt']}<|im_end|>\n<|im_start|>assistant\n"
        chosen_text = f"{item['chosen']}<|im_end|>"
        rejected_text = f"{item['rejected']}<|im_end|>"

        p_tokens = encode_fn(prompt_text)
        c_tokens = encode_fn(chosen_text)
        r_tokens = encode_fn(rejected_text)

        chosen_full = (p_tokens + c_tokens)[:self.max_seq_len]
        rejected_full = (p_tokens + r_tokens)[:self.max_seq_len]

        p_len_c = min(len(p_tokens), len(chosen_full))
        p_len_r = min(len(p_tokens), len(rejected_full))

        chosen_labels = [-100] * p_len_c + chosen_full[p_len_c:]
        rejected_labels = [-100] * p_len_r + rejected_full[p_len_r:]

        return {
            "chosen_input_ids": torch.tensor(chosen_full, dtype=torch.long),
            "chosen_labels": torch.tensor(chosen_labels, dtype=torch.long),
            "rejected_input_ids": torch.tensor(rejected_full, dtype=torch.long),
            "rejected_labels": torch.tensor(rejected_labels, dtype=torch.long),
        }
