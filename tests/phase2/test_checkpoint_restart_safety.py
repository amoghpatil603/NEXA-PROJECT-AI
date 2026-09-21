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

class TestCheckpointHardening(unittest.TestCase):
    """Tests for FIX 1 (post-save validation) and FIX 2 (safe replacement semantics)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ckpt_dir = os.path.join(self.test_dir, "checkpoints")
        self.log_dir = os.path.join(self.test_dir, "logs")
        self.config = TrainingConfig(
            batch_size=2,
            gradient_accumulation_steps=1,
            learning_rate=1e-3,
            max_steps=3,
            save_steps=1,   # save every step so we exercise validation at every step
            checkpoint_dir=self.ckpt_dir,
            log_dir=self.log_dir,
            seed=42
        )
        self.mgr = CheckpointManager(self.ckpt_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # TEST A: periodic checkpoint is validated after creation (FIX 1)     #
    # ------------------------------------------------------------------ #
    def test_periodic_checkpoint_validated_after_creation(self):
        """
        A. Running Trainer.train() with save_steps=1 must produce a
           valid checkpoint-N at every optimizer step, and Trainer
           must NOT raise even though validation is now active.
        """
        model = SimpleLinearModel()
        dataset = DummyDataset(size=10)
        trainer = Trainer(model, self.config, dataset)
        # Should complete without raising — all saves must pass validation
        trainer.train()
        self.assertGreaterEqual(trainer.optimizer_step, 1)
        # Every checkpoint written should be structurally valid
        for step in range(1, trainer.optimizer_step + 1):
            path = os.path.join(self.ckpt_dir, f"checkpoint-{step}")
            if os.path.exists(path):
                self.assertTrue(
                    self.mgr.is_checkpoint_valid(path),
                    f"checkpoint-{step} created by Trainer is not valid"
                )

    # ------------------------------------------------------------------ #
    # TEST B: corrupted checkpoint → training stops, no silent continue   #
    # ------------------------------------------------------------------ #
    def test_corrupted_checkpoint_raises_and_stops_training(self):
        """
        B. If is_checkpoint_valid returns False (simulating a structurally
           invalid checkpoint), training must halt with a RuntimeError.
           The error may be raised either in CheckpointManager.save() at
           the pre-promotion gate, or in Trainer._save_and_validate().
           Either way, training must NOT continue silently.
        """
        model = SimpleLinearModel()
        dataset = DummyDataset(size=10)
        trainer = Trainer(model, self.config, dataset)

        # Monkeypatch: make validation always report failure after save
        original_valid = trainer.checkpoint_manager.is_checkpoint_valid
        trainer.checkpoint_manager.is_checkpoint_valid = lambda path: False

        with self.assertRaises(RuntimeError) as ctx:
            trainer.train()

        err_msg = str(ctx.exception)
        # Accept either the CheckpointManager-level or Trainer-level error message
        self.assertTrue(
            "failed post-save validation" in err_msg or
            "failed validation before promotion" in err_msg or
            "Post-promotion validation failed" in err_msg,
            f"Expected a checkpoint validation failure message, got: {err_msg}"
        )

        # Restore so teardown works cleanly
        trainer.checkpoint_manager.is_checkpoint_valid = original_valid

    # ------------------------------------------------------------------ #
    # TEST C: previous trusted checkpoint survives a failed promotion      #
    # ------------------------------------------------------------------ #
    def test_trusted_checkpoint_preserved_on_promotion_failure(self):
        """
        C. When saving step-N for the second time (overwrite scenario),
           if the temporary checkpoint fails pre-promotion validation,
           the previously-trusted checkpoint-N must still be accessible.
        """
        model = SimpleLinearModel()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda s: 1.0)
        dataloader = DummyDataset()

        # Write a valid first version of checkpoint-2
        self.mgr.save(model, optimizer, scheduler, step=2, micro_step=2,
                      epoch=0, dataloader=dataloader, config=self.config)
        first_ckpt_path = os.path.join(self.ckpt_dir, "checkpoint-2")
        self.assertTrue(self.mgr.is_checkpoint_valid(first_ckpt_path),
                        "First checkpoint-2 must be valid before test starts")

        # Record the step value stored in the first checkpoint
        first_state = torch.load(
            os.path.join(first_ckpt_path, "training_state.pt"),
            map_location="cpu", weights_only=False
        )
        self.assertEqual(first_state["step"], 2)

        # Monkeypatch: make the FIRST call to is_checkpoint_valid return False
        # (simulates the tmp dir validation failing before promotion)
        call_count = [0]
        original_valid = self.mgr.is_checkpoint_valid

        def patched_valid(path):
            call_count[0] += 1
            if call_count[0] == 1:
                return False   # force pre-promotion failure
            return original_valid(path)

        self.mgr.is_checkpoint_valid = patched_valid

        with self.assertRaises(RuntimeError):
            self.mgr.save(model, optimizer, scheduler, step=2, micro_step=4,
                          epoch=0, dataloader=dataloader, config=self.config)

        self.mgr.is_checkpoint_valid = original_valid

        # The original checkpoint-2 must still be accessible and valid
        self.assertTrue(os.path.exists(first_ckpt_path),
                        "Trusted checkpoint-2 must still exist after failed overwrite")
        self.assertTrue(self.mgr.is_checkpoint_valid(first_ckpt_path),
                        "Trusted checkpoint-2 must still be valid after failed overwrite")
        recovered_state = torch.load(
            os.path.join(first_ckpt_path, "training_state.pt"),
            map_location="cpu", weights_only=False
        )
        self.assertEqual(recovered_state["step"], 2,
                         "Recovered checkpoint must contain the original step=2 state")

    # ------------------------------------------------------------------ #
    # TEST D: stale .tmp_checkpoint_* dirs cleaned on manager init         #
    # ------------------------------------------------------------------ #
    def test_stale_tmp_dirs_cleaned_on_init(self):
        """
        D. Any .tmp_checkpoint_* directories left over from a crashed
           previous run must be removed when CheckpointManager is
           re-instantiated (startup cleanup).
        """
        # Manually plant two stale tmp directories
        stale1 = os.path.join(self.ckpt_dir, ".tmp_checkpoint_99_aabbccdd")
        stale2 = os.path.join(self.ckpt_dir, ".tmp_checkpoint_100_deadbeef")
        os.makedirs(stale1, exist_ok=True)
        os.makedirs(stale2, exist_ok=True)
        with open(os.path.join(stale1, "partial.dat"), "w") as f:
            f.write("stale")
        with open(os.path.join(stale2, "partial.dat"), "w") as f:
            f.write("stale")

        # Also plant a valid checkpoint that must NOT be touched
        valid_path = os.path.join(self.ckpt_dir, "checkpoint-50")
        os.makedirs(valid_path, exist_ok=True)
        torch.save({'model_state_dict': {}}, os.path.join(valid_path, "training_state.pt"))
        self.config.save(os.path.join(valid_path, "training_config.json"))

        # Re-instantiate manager — startup cleanup must fire
        fresh_mgr = CheckpointManager(self.ckpt_dir)

        self.assertFalse(os.path.exists(stale1), "stale tmp dir 1 must be removed on init")
        self.assertFalse(os.path.exists(stale2), "stale tmp dir 2 must be removed on init")
        self.assertTrue(os.path.exists(valid_path), "valid checkpoint-50 must NOT be removed")
        self.assertTrue(fresh_mgr.is_checkpoint_valid(valid_path),
                        "checkpoint-50 must remain valid after cleanup")


if __name__ == "__main__":
    unittest.main()
