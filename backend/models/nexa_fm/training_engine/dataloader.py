try:
    import torch
except ImportError:
    torch = None
import json
import os
from typing import Iterator

class ShardDataLoader:
    def __init__(self, shard_dir: str, tokenizer, batch_size: int, max_length: int):
        self.shard_dir = shard_dir
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        self.max_length = max_length
        self.shard_files = sorted([os.path.join(shard_dir, f) for f in os.listdir(shard_dir) if f.endswith('.jsonl')]) if os.path.exists(shard_dir) else []

    def __iter__(self):
        batch_input_ids = []
        for shard_file in self.shard_files:
            with open(shard_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    text = item.get("text", "")
                    tokens = self.tokenizer.encode(text, add_special_tokens=True)
                    # chunking
                    for i in range(0, len(tokens), self.max_length):
                        chunk = tokens[i:i + self.max_length]
                        if len(chunk) < self.max_length:
                            chunk += [self.tokenizer.special_tokens["<PAD>"]] * (self.max_length - len(chunk))
                        
                        batch_input_ids.append(chunk)
                        
                        if len(batch_input_ids) == self.batch_size:
                            yield torch.tensor(batch_input_ids, dtype=torch.long)
                            batch_input_ids = []
