
import unittest
import torch
import numpy as np
import os
from pathlib import Path
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path('/tmp/test_loader_data')
        self.test_dir.mkdir(parents=True, exist_ok=True)
        # Create dummy shard
        self.data = np.arange(100, dtype=np.uint16)
        self.data.tofile(self.test_dir / 'shard_00000.bin')

    def test_dtype_and_shape(self):
        loader = ShardDataLoader(str(self.test_dir), batch_size=2, max_length=8, shuffle=False)
        batch = next(iter(loader))
        self.assertEqual(batch.dtype, torch.long)
        self.assertEqual(batch.shape, (2, 8))

    def test_deterministic_shuffle(self):
        # Create two shards
        np.arange(10).tofile(self.test_dir / 'shard_00001.bin')
        loader1 = ShardDataLoader(str(self.test_dir), batch_size=1, max_length=1, shuffle=True, seed=42)
        loader2 = ShardDataLoader(str(self.test_dir), batch_size=1, max_length=1, shuffle=True, seed=42)
        
        res1 = [b.item() for b in loader1]
        res2 = [b.item() for b in loader2]
        self.assertEqual(res1, res2)
