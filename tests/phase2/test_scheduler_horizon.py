import unittest
import os
import shutil
import tempfile
import torch

from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.trainer import Trainer
from tests.phase2.test_checkpoint_restart_safety import SimpleLinearModel, DummyDataset

class TestSchedulerHorizon(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ckpt_dir = os.path.join(self.test_dir, "checkpoints")
        self.log_dir = os.path.join(self.test_dir, "logs")

        # 1. Config with max_steps = 100000 and warmup_steps = 1000
        self.config = TrainingConfig(
            batch_size=2,
            gradient_accumulation_steps=1,
            learning_rate=1e-3, # Base LR
            warmup_steps=1000,
            max_steps=100000,
            save_steps=500,
            checkpoint_dir=self.ckpt_dir,
            log_dir=self.log_dir,
            seed=42
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def get_expected_lr_multiplier(self, step: int) -> float:
        """Mirror the LambdaLR logic from create_scheduler"""
        warmup = 1000
        max_steps = 100000
        if step < warmup:
            return float(step) / float(max(1, warmup))
        return max(0.0, float(max_steps - step) / float(max(1, max_steps - warmup)))

    def test_scheduler_horizon_preserved(self):
        """
        Verify the launcher does not poison the scheduler horizon by 
        constructing Trainer with max_steps=1.
        """
        model = SimpleLinearModel()
        # Ensure we have enough data to step without hitting end of epoch constantly
        dataset = DummyDataset(size=2000) 
        
        # 2. Construct Trainer with the 100000-step config
        trainer = Trainer(model, self.config, dataset)
        
        # Verify initial state
        self.assertEqual(trainer.config.max_steps, 100000)
        
        # 3. One-step gate executes only optimizer step 1
        trainer.train(max_steps_override=1)
        self.assertEqual(trainer.optimizer_step, 1)
        
        # 4. Checkpoint-1 is saved (simulating the gate manually, or Trainer does it if in early_save_steps)
        # We'll explicitly save it if it didn't
        ckpt_path = os.path.join(self.ckpt_dir, "checkpoint-1")
        if not os.path.exists(ckpt_path):
            trainer._save_and_validate()
            
        self.assertTrue(os.path.exists(ckpt_path))
        
        # 5. After resuming, the scheduler continues with the 100000-step schedule
        # Create a new trainer to simulate the restart after checkpoint-1 validation
        model2 = SimpleLinearModel()
        trainer2 = Trainer(model2, self.config, dataset)
        resumed = trainer2.resume_from_checkpoint(ckpt_path)
        self.assertTrue(resumed)
        self.assertEqual(trainer2.optimizer_step, 1)
        self.assertEqual(trainer2.config.max_steps, 100000)
        
        # Helper to get LR at a specific step
        def check_lr_at_step(target_step):
            # Step until we reach the target
            # Note: We step the scheduler manually here for testing the schedule without running full loops
            while trainer2.optimizer_step < target_step:
                trainer2.scheduler.step()
                trainer2.optimizer_step += 1
            
            # The current LR
            current_lr = trainer2.scheduler.get_last_lr()[0]
            expected_multiplier = self.get_expected_lr_multiplier(target_step)
            expected_lr = self.config.learning_rate * expected_multiplier
            
            self.assertAlmostEqual(
                current_lr, 
                expected_lr, 
                places=6, 
                msg=f"LR mismatch at step {target_step}"
            )
        
        # 6. Verify learning-rate values around key steps
        # We are at step 1 currently
        check_lr_at_step(1)
        check_lr_at_step(10)
        check_lr_at_step(100)
        check_lr_at_step(1000) # peak
        check_lr_at_step(50000)
        check_lr_at_step(100000)

if __name__ == "__main__":
    unittest.main()
