
import torch
from torch.utils.data import Sampler
import math

class NexaDeterministicSampler(Sampler):
    def __init__(self, dataset, batch_size, epoch=0, seed=42, shuffle=True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.epoch = epoch
        self.seed = seed
        self.shuffle = shuffle
        self.num_samples = len(dataset)
        
    def __iter__(self):
        if self.shuffle:
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch)
            indices = torch.randperm(self.num_samples, generator=g).tolist()
        else:
            indices = list(range(self.num_samples))
            
        return iter(indices)
        
    def __len__(self):
        return self.num_samples
        
    def get_resume_state(self):
        return {
            "epoch": self.epoch,
            "seed": self.seed
        }
