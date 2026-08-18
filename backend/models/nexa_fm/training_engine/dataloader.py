import torch
import numpy as np
from pathlib import Path

class ShardDataLoader:
    def __init__(self, shard_dir, batch_size=1, max_length=2048, shuffle=True, seed=42, start_batch_idx=0):
        self.shard_dir = Path(shard_dir)
        self.batch_size = batch_size
        self.max_length = max_length
        self.start_batch_idx = start_batch_idx
        self.shards = sorted(list(self.shard_dir.glob('*.bin')))

    def __iter__(self):
        current_start_batch = self.start_batch_idx
        for shard_path in self.shards:
            data = np.memmap(shard_path, dtype=np.uint16, mode='r')
            num_sequences = len(data) // self.max_length
            sequences = data[:num_sequences * self.max_length].reshape(-1, self.max_length)
            start_row = (current_start_batch * self.batch_size)
            for i in range(start_row, len(sequences), self.batch_size):
                batch = sequences[i:i + self.batch_size]
                yield torch.from_numpy(batch.astype(np.int64))
            current_start_batch = 0 # Reset for subsequent shards
