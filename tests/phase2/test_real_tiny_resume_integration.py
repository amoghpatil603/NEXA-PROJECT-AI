import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import torch

class TestRealTinyResumeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ckpt_dir = os.path.join(self.test_dir, "ckpts")
        self.log_dir = os.path.join(self.test_dir, "logs")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_real_tiny_cross_process_resume_and_step(self):
        script_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{os.getcwd()}")
import torch
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer

mode = sys.argv[1]
model_cfg = NexaConfig.tiny()
model = NexaTransformer(model_cfg)
config = TrainingConfig(
    batch_size=1,
    gradient_accumulation_steps=1,
    learning_rate=3e-4,
    max_steps=2 if mode == 'p1' else 3,
    save_steps=1,
    checkpoint_dir=r"{self.ckpt_dir}",
    log_dir=r"{self.log_dir}",
    dataset_dir="data/shards",
    seed=42
)
dl = ShardDataLoader("data/shards", batch_size=1, max_length=model_cfg.max_seq_len, shuffle=False)
trainer = Trainer(model, config, dl)

if mode == "p1":
    trainer.train()
    if trainer.optimizer_step != 2:
        sys.exit(10)
    sys.exit(0)
elif mode == "p2":
    resumed = trainer.resume_from_checkpoint()
    if not resumed:
        sys.exit(20)
    if trainer.optimizer_step != 2:
        sys.exit(21)
    trainer.train()
    if trainer.optimizer_step != 3:
        sys.exit(22)
    sys.exit(0)
"""
        run_file = os.path.join(self.test_dir, "runner.py")
        with open(run_file, "w", encoding="utf-8") as f:
            f.write(script_code)

        # Run Process 1 (trains steps 1 and 2, saves checkpoint-2)
        res1 = subprocess.run([sys.executable, run_file, "p1"], capture_output=True, text=True, cwd=os.getcwd())
        self.assertEqual(res1.returncode, 0, f"P1 failed: {res1.stderr}\nStdout: {res1.stdout}")
        self.assertTrue(os.path.exists(os.path.join(self.ckpt_dir, "checkpoint-2")))

        # Run Process 2 (resumes from checkpoint-2, trains step 3)
        res2 = subprocess.run([sys.executable, run_file, "p2"], capture_output=True, text=True, cwd=os.getcwd())
        self.assertEqual(res2.returncode, 0, f"P2 failed: {res2.stderr}\nStdout: {res2.stdout}")
        self.assertTrue(os.path.exists(os.path.join(self.ckpt_dir, "checkpoint-3")))

if __name__ == "__main__":
    unittest.main()
