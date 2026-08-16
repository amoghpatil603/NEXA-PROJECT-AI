import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

class DatasetSharder:
    """
    Production Binary Sharder: Writes tokenized sequences into uint16 binary shards.
    Ensures memory efficiency, deterministic naming, and input validation.
    """
    def __init__(self, output_dir: str, shard_size: int = 100000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shard_size = shard_size
        self.current_shard_idx = 0
        self.buffer = []
        self.total_tokens = 0

    def write(self, tokens: List[int]):
        if any(t < 0 or t > 65535 for t in tokens):
            raise ValueError("Token IDs must fit in uint16 (0-65535)")
        self.buffer.extend(tokens)
        self.total_tokens += len(tokens)
        while len(self.buffer) >= self.shard_size:
            self._flush()

    def _flush(self):
        shard_path = self.output_dir / f"shard_{self.current_shard_idx:05d}.bin"
        data = np.array(self.buffer[:self.shard_size], dtype=np.uint16)
        data.tofile(shard_path)
        self.buffer = self.buffer[self.shard_size:]
        self.current_shard_idx += 1

    def close(self) -> Dict[str, Any]:
        if self.buffer:
            shard_path = self.output_dir / f"shard_{self.current_shard_idx:05d}.bin"
            data = np.array(self.buffer, dtype=np.uint16)
            data.tofile(shard_path)
            self.current_shard_idx += 1
            self.buffer = []
        return {
            "shard_count": self.current_shard_idx,
            "total_tokens": self.total_tokens,
            "shard_format": "uint16_binary"
        }