
import unittest
import os
import numpy as np
from pathlib import Path
from backend.models.nexa_fm.data_pipeline.sharding import DatasetSharder

class TestSharding(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path('/tmp/test_shards')
        if self.test_dir.exists():
            for f in self.test_dir.glob('*'): f.unlink()
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def test_binary_creation(self):
        tokens = [1, 2, 3, 4, 5, 100, 1000]
        sharder = DatasetSharder(str(self.test_dir), shard_size=100)
        sharder.write(tokens)
        stats = sharder.close()
        
        shard_path = self.test_dir / 'shard_00000.bin'
        self.assertTrue(shard_path.exists())
        self.assertEqual(stats['total_tokens'], len(tokens))
        
        # Verify dtype and values
        data = np.fromfile(shard_path, dtype=np.uint16)
        np.testing.assert_array_equal(data, np.array(tokens, dtype=np.uint16))

    def test_invalid_ids(self):
        sharder = DatasetSharder(str(self.test_dir))
        with self.assertRaises(ValueError):
            sharder.write([70000]) # Over uint16

    def test_multiple_shards(self):
        sharder = DatasetSharder(str(self.test_dir), shard_size=10)
        tokens = list(range(25))
        sharder.write(tokens)
        stats = sharder.close()
        
        self.assertEqual(stats['shard_count'], 3)
        # Verify full reconstruction
        all_data = []
        for i in range(3):
            data = np.fromfile(self.test_dir / f'shard_{i:05d}.bin', dtype=np.uint16)
            all_data.extend(data.tolist())
        self.assertEqual(all_data, tokens)
