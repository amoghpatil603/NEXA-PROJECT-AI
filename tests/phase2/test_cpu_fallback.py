import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import torch
import torch.nn as nn
from pathlib import Path

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer
from scripts.train_pretrain import build_parser, create_pretraining_setup

class DummyTinyDataset:
    def __init__(self, batch_size=1, max_length=16):
        self.shards = []
        self.batch_size = batch_size
        self.max_length = max_length
        self.current_shard_idx = 0
        self.current_batch_idx = 0
        torch.manual_seed(42)
        self.data = [torch.randint(0, 100, (batch_size, max_length)) for _ in range(5)]

    def __iter__(self):
        for idx, b in enumerate(self.data):
            self.current_batch_idx = idx
            yield b

class TestCPUFallback(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ckpt_dir = os.path.join(self.test_dir, "ckpts")
        self.log_dir = os.path.join(self.test_dir, "logs")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cpu_device_selection(self):
        config = TrainingConfig(checkpoint_dir=self.ckpt_dir, log_dir=self.log_dir)
        model = nn.Linear(8, 8)
        dataset = DummyTinyDataset()
        trainer = Trainer(model, config, dataset)
        
        # When CUDA is not available on CPU host, device must be CPU
        if not torch.cuda.is_available():
            self.assertEqual(trainer.device.type, "cpu")

    def test_cpu_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(["--dry-run", "--batch-size", "1", "--dataset-dir", "data/shards"])
        model, config, dataloader = create_pretraining_setup(args)
        
        self.assertIsNotNone(dataloader)
        trainer = Trainer(model, config, dataloader)
        success = trainer.dry_run()
        self.assertTrue(success)

    def test_cpu_1_to_2_step_training_and_checkpoint(self):
        config = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=3e-4,
            max_steps=2,
            save_steps=1,
            log_steps=1,
            checkpoint_dir=self.ckpt_dir,
            log_dir=self.log_dir,
            dataset_dir="data/shards",
            seed=42
        )
        model_cfg = NexaConfig.tiny()
        model = NexaTransformer(model_cfg)
        dl = ShardDataLoader("data/shards", batch_size=1, max_length=model_cfg.max_seq_len, shuffle=False)
        
        trainer = Trainer(model, config, dl)
        trainer.train()

        self.assertEqual(trainer.optimizer_step, 2)
        self.assertTrue(os.path.exists(os.path.join(self.ckpt_dir, "checkpoint-1")))
        self.assertTrue(os.path.exists(os.path.join(self.ckpt_dir, "checkpoint-2")))

    def test_cpu_long_training_safeguard(self):
        # When CUDA is unavailable and max_steps > 10, CLI must reject execution without explicit override
        if not torch.cuda.is_available():
            cmd_reject = [
                sys.executable,
                "scripts/train_pretrain.py",
                "--max-steps", "1000",
                "--checkpoint-dir", self.ckpt_dir,
                "--log-dir", self.log_dir
            ]
            res_reject = subprocess.run(cmd_reject, capture_output=True, text=True, cwd=os.getcwd())
            self.assertNotEqual(res_reject.returncode, 0)
            self.assertIn("CUDA is unavailable", res_reject.stdout + res_reject.stderr)

            # Providing --allow-cpu-long-training overrides safeguard
            cmd_allow = [
                sys.executable,
                "scripts/train_pretrain.py",
                "--max-steps", "2",
                "--allow-cpu-long-training",
                "--checkpoint-dir", self.ckpt_dir,
                "--log-dir", self.log_dir
            ]
            res_allow = subprocess.run(cmd_allow, capture_output=True, text=True, cwd=os.getcwd())
            self.assertEqual(res_allow.returncode, 0)

    def test_cuda_specific_logic_safely_skipped_on_cpu(self):
        # On CPU, scaler is disabled and CUDA-specific methods are safely bypassed
        config = TrainingConfig(mixed_precision=True, checkpoint_dir=self.ckpt_dir, log_dir=self.log_dir)
        model = nn.Linear(8, 8)
        dataset = DummyTinyDataset()
        trainer = Trainer(model, config, dataset)

        if trainer.device.type == "cpu":
            # Scaler should be None or not enabled for CUDA
            if trainer.scaler is not None:
                self.assertFalse(trainer.scaler.is_enabled())

if __name__ == "__main__":
    unittest.main()
