import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import torch
import torch.nn as nn
import numpy as np

from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.checkpoints import CheckpointManager
from backend.models.nexa_fm.training_engine.trainer import Trainer

class SimpleLinearModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(10, 8)
        self.head = nn.Linear(8, 10)

    def forward(self, x, targets=None):
        h = self.embedding(x)
        logits = self.head(h)
        if targets is not None:
            import torch.nn.functional as F
            loss = F.cross_entropy(logits.view(-1, 10), targets.view(-1))
            return logits, loss
        return logits

class DummyDataset:
    def __init__(self, size=20):
        self.shards = []
        self.batch_size = 2
        self.max_length = 8
        self.data = [torch.randint(0, 10, (2, 8)) for _ in range(size)]
        self.current_shard_idx = 0
        self.current_batch_idx = 0

    def __iter__(self):
        for idx, batch in enumerate(self.data):
            self.current_batch_idx = idx
            yield batch

class TestCheckpointRestartSafety(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ckpt_dir = os.path.join(self.test_dir, "checkpoints")
        self.log_dir = os.path.join(self.test_dir, "logs")
        self.config = TrainingConfig(
            batch_size=2,
            gradient_accumulation_steps=1,
            learning_rate=1e-3,
            max_steps=5,
            save_steps=2,
            checkpoint_dir=self.ckpt_dir,
            log_dir=self.log_dir,
            seed=42
        )
        self.mgr = CheckpointManager(self.ckpt_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_no_checkpoint_returns_none(self):
        self.assertIsNone(self.mgr.get_latest_checkpoint())

    def test_numerical_ordering_discovery(self):
        # Create directories in non-alphabetical step order
        for step in [20, 1000, 200, 50]:
            path = os.path.join(self.ckpt_dir, f"checkpoint-{step}")
            os.makedirs(path, exist_ok=True)
            # Write valid state and config
            torch.save({'model_state_dict': {}}, os.path.join(path, "training_state.pt"))
            self.config.save(os.path.join(path, "training_config.json"))

        latest = self.mgr.get_latest_checkpoint()
        self.assertIsNotNone(latest)
        self.assertTrue(latest.endswith("checkpoint-1000"))

    def test_incomplete_temp_checkpoint_ignored(self):
        # Create a valid checkpoint-100 and an incomplete temporary .tmp_checkpoint_200
        path_valid = os.path.join(self.ckpt_dir, "checkpoint-100")
        os.makedirs(path_valid, exist_ok=True)
        torch.save({'model_state_dict': {}}, os.path.join(path_valid, "training_state.pt"))
        self.config.save(os.path.join(path_valid, "training_config.json"))

        tmp_dir = os.path.join(self.ckpt_dir, ".tmp_checkpoint_200_abc")
        os.makedirs(tmp_dir, exist_ok=True)
        with open(os.path.join(tmp_dir, "corrupt.tmp"), "w") as f:
            f.write("partial")

        latest = self.mgr.get_latest_checkpoint()
        self.assertEqual(latest, path_valid)

    def test_corrupted_latest_checkpoint_fallback(self):
        # Create valid checkpoint-100
        path_100 = os.path.join(self.ckpt_dir, "checkpoint-100")
        os.makedirs(path_100, exist_ok=True)
        torch.save({'model_state_dict': {}}, os.path.join(path_100, "training_state.pt"))
        self.config.save(os.path.join(path_100, "training_config.json"))

        # Create corrupted checkpoint-200 (truncated state file)
        path_200 = os.path.join(self.ckpt_dir, "checkpoint-200")
        os.makedirs(path_200, exist_ok=True)
        with open(os.path.join(path_200, "training_state.pt"), "wb") as f:
            f.write(b"CORRUPTED_TRUNCATED_BYTES")
        self.config.save(os.path.join(path_200, "training_config.json"))

        # CheckpointManager should skip 200 and return 100
        latest = self.mgr.get_latest_checkpoint()
        self.assertEqual(latest, path_100)

    def test_identity_guard_enforcement(self):
        model = SimpleLinearModel()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda s: 1.0)
        dataloader = DummyDataset()

        # Save checkpoint with config
        self.mgr.save(model, optimizer, scheduler, step=2, micro_step=2, epoch=0, dataloader=dataloader, config=self.config)
        ckpt_path = os.path.join(self.ckpt_dir, "checkpoint-2")

        # Test mismatched dataset_version
        bad_config_1 = TrainingConfig(
            checkpoint_dir=self.ckpt_dir,
            dataset_version="9.9.9-mismatch",
            dataset_content_hash=self.config.dataset_content_hash,
            tokenizer_identity=self.config.tokenizer_identity,
            tokenizer_config_identity=self.config.tokenizer_config_identity
        )
        with self.assertRaises(ValueError) as ctx:
            self.mgr.load(ckpt_path, model, config=bad_config_1)
        self.assertIn("Dataset version mismatch", str(ctx.exception))

        # Test mismatched tokenizer_identity
        bad_config_2 = TrainingConfig(
            checkpoint_dir=self.ckpt_dir,
            dataset_version=self.config.dataset_version,
            dataset_content_hash=self.config.dataset_content_hash,
            tokenizer_identity="bad_tokenizer_hash_12345",
            tokenizer_config_identity=self.config.tokenizer_config_identity
        )
        with self.assertRaises(ValueError) as ctx:
            self.mgr.load(ckpt_path, model, config=bad_config_2)
        self.assertIn("Tokenizer identity mismatch", str(ctx.exception))

    def test_fresh_process_cross_session_simulation(self):
        """Simulates Colab termination across 2 isolated Python processes."""
        script = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{os.getcwd()}")
import torch
import torch.nn as nn
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.trainer import Trainer

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(10, 8)
        self.head = nn.Linear(8, 10)
    def forward(self, x, targets=None):
        h = self.emb(x)
        logits = self.head(h)
        if targets is not None:
            import torch.nn.functional as F
            loss = F.cross_entropy(logits.view(-1, 10), targets.view(-1))
            return logits, loss
        return logits

class Dataset:
    def __init__(self):
        self.shards = []
        self.batch_size = 2
        self.max_length = 8
        self.current_shard_idx = 0
        self.current_batch_idx = 0
    def __iter__(self):
        torch.manual_seed(42)
        for i in range(10):
            self.current_batch_idx = i
            yield torch.randint(0, 10, (2, 8))

mode = sys.argv[1]
ckpt_dir = r"{self.ckpt_dir}"

config = TrainingConfig(
    batch_size=2,
    gradient_accumulation_steps=1,
    learning_rate=1e-3,
    max_steps=2 if mode == 'session1' else 4,
    save_steps=2,
    checkpoint_dir=ckpt_dir,
    log_dir=r"{self.log_dir}",
    seed=42
)

model = Model()
dataset = Dataset()
trainer = Trainer(model, config, dataset)

if mode == 'session1':
    # Session 1: Train 2 steps and save checkpoint
    trainer.train()
    sys.exit(0)
elif mode == 'session2':
    # Session 2: Auto-resume from latest checkpoint and finish to step 4
    resumed = trainer.resume_from_checkpoint()
    if not resumed:
        sys.exit(2)
    if trainer.optimizer_step != 2:
        sys.exit(3)
    trainer.train()
    if trainer.optimizer_step != 4:
        sys.exit(4)
    sys.exit(0)
"""
        script_file = os.path.join(self.test_dir, "run_sim.py")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)

        # Execute Session 1 in subprocess
        res1 = subprocess.run([sys.executable, script_file, "session1"], capture_output=True, text=True, cwd=os.getcwd())
        self.assertEqual(res1.returncode, 0, f"Session 1 failed: {res1.stderr}")

        # Verify checkpoint was written
        self.assertTrue(os.path.exists(os.path.join(self.ckpt_dir, "checkpoint-2")))

        # Execute Session 2 in fresh independent subprocess
        res2 = subprocess.run([sys.executable, script_file, "session2"], capture_output=True, text=True, cwd=os.getcwd())
        self.assertEqual(res2.returncode, 0, f"Session 2 failed with code {res2.returncode}: {res2.stderr}\nStdout: {res2.stdout}")

if __name__ == "__main__":
    unittest.main()
