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
    def __init__(self, shard_dir: str, batch_size: int = 1, max_length: int = 2048, shuffle: bool = True, seed: int = 42, start_shard_idx: int = 0, start_batch_idx: int = 0, drop_last: bool = False):
        self.shard_dir = Path(shard_dir)
        self.batch_size = batch_size
        self.max_length = max_length
        self.shuffle = shuffle
        self.seed = seed
        self.start_shard_idx = start_shard_idx
        self.start_batch_idx = start_batch_idx
        self.drop_last = drop_last
        self.current_shard_idx = start_shard_idx
        self.current_batch_idx = start_batch_idx
        self.shards = sorted(list(self.shard_dir.glob("*.bin")))
        if not self.shards:
            self.shards = sorted(list(self.shard_dir.glob("**/*.bin")))
        if not self.shards:
            raise FileNotFoundError(f"No shards found in {shard_dir}")

    def __iter__(self) -> Iterator[torch.Tensor]:
        indices = np.arange(len(self.shards))
        if self.shuffle:
            rng = np.random.default_rng(self.seed)
            rng.shuffle(indices)

        for s_idx in range(self.start_shard_idx, len(indices)):
            idx = indices[s_idx]
            shard_path = self.shards[idx]
            # Zero-copy memory mapping
            data = np.memmap(shard_path, dtype=np.uint16, mode='r')
            num_tokens = len(data)
            num_sequences = num_tokens // self.max_length
            if num_sequences == 0:
                if num_tokens > 0:
                    padded = np.zeros(self.max_length, dtype=np.uint16)
                    padded[:num_tokens] = data[:]
                    sequences = padded.reshape(1, self.max_length)
                else:
                    continue
            else:
                # Avoid full copy: reshape a slice/view of memmap array directly
                sequences = data[:num_sequences * self.max_length].reshape(-1, self.max_length)
            
            # Start from the start_batch_idx if we are in the starting shard
            start_b = self.start_batch_idx if s_idx == self.start_shard_idx else 0
            
            for i in range(start_b, len(sequences), self.batch_size):
                batch = sequences[i:i + self.batch_size]
                if self.drop_last and len(batch) < self.batch_size:
                    continue
                if len(batch) == 0:
                    continue
                self.current_shard_idx = s_idx
                self.current_batch_idx = i
                # Cast to int64 for embeddings input mapping in PyTorch
                yield torch.from_numpy(batch.astype(np.int64))
            
            # Reset start_batch_idx for subsequent shards
            self.start_batch_idx = 0
            
        # Reset start_shard_idx for subsequent iterations/epochs
        self.start_shard_idx = 0