import unittest
import os
import sys
import tempfile
import numpy as np
import torch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer

class TestPretrainResumeBoundaries(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.dataset_dir = os.path.join(self.tmp_dir, "shards")
        self.checkpoint_dir = os.path.join(self.tmp_dir, "checkpoints")
        self.log_dir = os.path.join(self.tmp_dir, "logs")
        os.makedirs(self.dataset_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Create 3 shards with known deterministic sequence data
        # Shard 0: 4 sequences of length 64
        # Shard 1: 4 sequences of length 64
        # Shard 2: 4 sequences of length 64
        self.max_len = 64
        for s_idx in range(3):
            data = np.arange(4 * self.max_len, dtype=np.uint16) + (s_idx * 1000)
            data = data % 7000  # keep well within vocab
            with open(os.path.join(self.dataset_dir, f"shard_{s_idx:05d}.bin"), "wb") as f:
                f.write(data.tobytes())

    def test_within_shard_resume_batch_tensor_equality(self):
        # 1. Uninterrupted run: read all batches for 3 steps (batch_size=1)
        dl_uninterrupted = ShardDataLoader(self.dataset_dir, batch_size=1, max_length=self.max_len, shuffle=False)
        batches_uninterrupted = []
        for i, b in enumerate(dl_uninterrupted):
            batches_uninterrupted.append(b.clone())
            if i >= 3:
                break

        # 2. Stepped run: run 1 step, save checkpoint, advance cursor, and verify next batch
        cfg = NexaConfig(
            vocab_size=8000,
            max_seq_len=self.max_len,
            d_model=64,
            n_layers=2,
            n_heads=2,
            d_ff=128
        )
        model = NexaTransformer(cfg)
        t_cfg = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=1e-4,
            max_steps=1,
            save_steps=1,
            checkpoint_dir=self.checkpoint_dir,
            log_dir=self.log_dir,
            dataset_dir=self.dataset_dir,
            seed=42
        )

        dl_run1 = ShardDataLoader(self.dataset_dir, batch_size=1, max_length=self.max_len, shuffle=False)
        trainer1 = Trainer(model, t_cfg, dl_run1)
        trainer1.train()

        self.assertEqual(trainer1.optimizer_step, 1)

        # 3. Resume in a fresh loader & trainer
        model2 = NexaTransformer(cfg)
        dl_resumed = ShardDataLoader(self.dataset_dir, batch_size=1, max_length=self.max_len, shuffle=False)
        t_cfg2 = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=1e-4,
            max_steps=3,
            save_steps=1,
            checkpoint_dir=self.checkpoint_dir,
            log_dir=self.log_dir,
            dataset_dir=self.dataset_dir,
            seed=42
        )
        trainer2 = Trainer(model2, t_cfg2, dl_resumed)
        resumed = trainer2.resume_from_checkpoint()
        self.assertTrue(resumed)
        self.assertEqual(trainer2.optimizer_step, 1)

        # Fetch the very first batch produced by resumed loader
        resumed_iter = iter(dl_resumed)
        first_resumed_batch = next(resumed_iter)

        # It must exactly match the second batch of the uninterrupted run!
        self.assertTrue(
            torch.equal(batches_uninterrupted[1], first_resumed_batch),
            "Resumed next-batch tensor does not match uninterrupted next-batch tensor!"
        )

    def test_exact_shard_boundary_resume(self):
        # Shard has 4 sequences. If we process 4 batches with batch_size=1, the 5th batch must be from shard 1, batch 0.
        dl = ShardDataLoader(self.dataset_dir, batch_size=1, max_length=self.max_len, shuffle=False)
        
        # Cursor at shard 0, batch 3 (the 4th sequence, last in shard 0)
        next_shard, next_batch = dl.advance_cursor(curr_shard=0, curr_batch=3)
        self.assertEqual(next_shard, 1)
        self.assertEqual(next_batch, 0)

        # Cursor at shard 0, batch 2 -> advances to shard 0, batch 3
        next_shard, next_batch = dl.advance_cursor(curr_shard=0, curr_batch=2)
        self.assertEqual(next_shard, 0)
        self.assertEqual(next_batch, 3)

if __name__ == "__main__":
    unittest.main()
