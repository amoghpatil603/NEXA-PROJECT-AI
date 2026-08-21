import unittest
import sys
import tempfile
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader

class TestDatasetDiscoveryAndErrors(unittest.TestCase):
    def test_missing_directory_raises_clear_error(self):
        non_existent_path = Path(tempfile.gettempdir()) / "nexa_missing_dir_xyz_123"
        with self.assertRaises(FileNotFoundError) as ctx:
            ShardDataLoader(non_existent_path)
        self.assertIn("Dataset directory does not exist", str(ctx.exception))

    def test_empty_directory_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileNotFoundError) as ctx:
                ShardDataLoader(tmp_dir)
            self.assertIn("No binary shards (*.bin) found", str(ctx.exception))

    def test_nested_train_directory_discovery(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            train_dir = Path(tmp_dir) / "train"
            val_dir = Path(tmp_dir) / "validation"
            train_dir.mkdir(parents=True)
            val_dir.mkdir(parents=True)

            # Create dummy uint16 bin shards (2048 tokens each = 4096 bytes)
            dummy_data = np.ones(2048, dtype=np.uint16)
            for i in range(3):
                with open(train_dir / f"shard_{i:05d}.bin", "wb") as f:
                    f.write(dummy_data.tobytes())

            for i in range(2):
                with open(val_dir / f"shard_{i:05d}.bin", "wb") as f:
                    f.write(dummy_data.tobytes())

            loader = ShardDataLoader(tmp_dir, batch_size=1, max_length=2048, shuffle=False)
            self.assertEqual(len(loader.shards), 3)
            self.assertTrue(all("train" in str(s) for s in loader.shards))

    def test_flat_directory_discovery(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_data = np.ones(1024, dtype=np.uint16)
            for i in range(2):
                with open(Path(tmp_dir) / f"shard_{i:05d}.bin", "wb") as f:
                    f.write(dummy_data.tobytes())

            loader = ShardDataLoader(tmp_dir, batch_size=1, max_length=512, shuffle=False)
            self.assertEqual(len(loader.shards), 2)

    def test_empty_shard_file_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_file = Path(tmp_dir) / "empty_shard_00000.bin"
            empty_file.touch()

            with self.assertRaises(ValueError) as ctx:
                ShardDataLoader(tmp_dir)
            self.assertIn("Found empty binary shard file (0 bytes)", str(ctx.exception))

    def test_zero_copy_memmap_streaming(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a 4096 token shard (2 sequences of 2048)
            seqs = np.arange(4096, dtype=np.uint16) % 500
            with open(Path(tmp_dir) / "shard_00000.bin", "wb") as f:
                f.write(seqs.tobytes())

            loader = ShardDataLoader(tmp_dir, batch_size=1, max_length=2048, shuffle=False)
            batches = list(loader)
            self.assertEqual(len(batches), 2)
            self.assertEqual(list(batches[0].shape), [1, 2048])
            self.assertEqual(list(batches[1].shape), [1, 2048])

if __name__ == "__main__":
    unittest.main()
