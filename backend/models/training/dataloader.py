
from torch.utils.data import DataLoader
from .dataset import NexaDataset
from .sampler import NexaDeterministicSampler
import torch

def collate_nexa(batch):
    # batch is list of 1D tensors of length 257
    stacked = torch.stack(batch)
    input_ids = stacked[:, :-1].contiguous()
    targets = stacked[:, 1:].contiguous()
    return input_ids, targets

def create_dataloader(split_dir, batch_size, stride=256, seq_len=257, pad_id=4, shuffle=True, epoch=0, seed=42, num_workers=0):
    dataset = NexaDataset(split_dir, stride, seq_len, pad_id)
    sampler = NexaDeterministicSampler(dataset, batch_size, epoch, seed, shuffle)
    loader = DataLoader(
        dataset, 
        batch_size=batch_size, 
        sampler=sampler, 
        collate_fn=collate_nexa,
        num_workers=num_workers,
        pin_memory=False
    )
    return loader
