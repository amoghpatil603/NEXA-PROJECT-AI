
import unittest
import torch
import numpy as np
from pathlib import Path
from backend.models.nexa_fm.data_pipeline.sharding import DatasetSharder
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader

class TestRoundTrip(unittest.TestCase):
    def test_binary_roundtrip(self):
        test_dir = Path('/tmp/roundtrip_test')
        test_dir.mkdir(parents=True, exist_ok=True)
        tokens = list(range(1000))
        
        sharder = DatasetSharder(str(test_dir), shard_size=100)
        sharder.write(tokens)
        sharder.close()

        loader = ShardDataLoader(str(test_dir), batch_size=1, max_length=10, shuffle=False)
        reconstructed = []
        for batch in loader:
            reconstructed.extend(batch.view(-1).tolist())
            
        # Match values (ShardDataLoader reshapes into max_length)
        self.assertEqual(reconstructed[:1000], tokens)
