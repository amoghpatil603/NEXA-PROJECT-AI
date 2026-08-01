
import numpy as np
import torch
from torch.utils.data import Dataset
from pathlib import Path

class NexaDataset(Dataset):
    def __init__(self, split_dir, stride=256, seq_len=257, pad_id=4):
        self.split_dir = Path(split_dir)
        self.stride = stride
        self.seq_len = seq_len
        self.pad_id = pad_id
        
        self.shards = sorted(self.split_dir.glob("*.bin"))
        self.lengths = []
        self.samples = []
        
        for i, shard in enumerate(self.shards):
            length = shard.stat().st_size // 2
            self.lengths.append(length)
            
            if length < self.seq_len:
                self.samples.append((i, 0))
            else:
                num_samples = (length - self.seq_len) // self.stride + 1
                for j in range(num_samples):
                    self.samples.append((i, j * self.stride))
                    
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        shard_idx, start = self.samples[idx]
        shard = self.shards[shard_idx]
        length = self.lengths[shard_idx]
        
        # Read from file to keep memory bounded
        with open(shard, "rb") as f:
            if length < self.seq_len:
                data = f.read(length * 2)
                tokens = np.frombuffer(data, dtype=np.uint16).astype(np.int64).tolist()
                pad_len = self.seq_len - length
                tokens.extend([self.pad_id] * pad_len)
            else:
                f.seek(start * 2)
                data = f.read(self.seq_len * 2)
                tokens = np.frombuffer(data, dtype=np.uint16).astype(np.int64).tolist()
                
        return torch.tensor(tokens, dtype=torch.long)
