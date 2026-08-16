import torch
import numpy as np
import os
from pathlib import Path
from typing import Iterator

class ShardDataLoader:
    """
    Production DataLoader: Reads uint16 binary shards using memory-mapping.
    Produces (batch_size, sequence_length) torch.long tensors.
    """
    def __init__(self, shard_dir: str, batch_size: int = 1, max_length: int = 2048, shuffle: bool = True, seed: int = 42):
        self.shard_dir = Path(shard_dir)
        self.batch_size = batch_size
        self.max_length = max_length
        self.shuffle = shuffle
        self.seed = seed
        self.shards = sorted(list(self.shard_dir.glob("*.bin")))
        if not self.shards:
            raise FileNotFoundError(f"No shards found in {shard_dir}")

    def __iter__(self) -> Iterator[torch.Tensor]:
        indices = np.arange(len(self.shards))
        if self.shuffle:
            rng = np.random.default_rng(self.seed)
            rng.shuffle(indices)

        for idx in indices:
            shard_path = self.shards[idx]
            # Zero-copy memory mapping
            data = np.memmap(shard_path, dtype=np.uint16, mode='r')
            num_tokens = len(data)
            num_sequences = num_tokens // self.max_length
            if num_sequences == 0: continue

            sequences = np.array(data[:num_sequences * self.max_length]).reshape(-1, self.max_length)
            for i in range(0, len(sequences), self.batch_size):
                batch = sequences[i:i + self.batch_size]
                if len(batch) < self.batch_size: continue
                yield torch.from_numpy(batch.astype(np.int64))