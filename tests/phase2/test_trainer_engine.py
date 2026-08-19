import unittest
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import tempfile
import os
import shutil
from pathlib import Path

from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.trainer import Trainer

class TinyModel(nn.Module):
    def __init__(self, vocab_size=10, hidden_dim=8):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        self.linear = nn.Linear(hidden_dim, vocab_size)

    def forward(self, input_ids):
        x = self.embedding(input_ids)
        logits = self.linear(x)
        return logits

class DummyDataset:
    def __init__(self, num_samples=10, seq_len=16, vocab_size=10):
        # Generate deterministic data
        torch.manual_seed(42)
        self.data = torch.randint(0, vocab_size, (num_samples, seq_len))

    def __iter__(self):
        for sample in self.data:
            yield sample.unsqueeze(0) # batch_size=1

class TestTrainerEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=1e-3,
            weight_decay=0.0,
            warmup_steps=0,
            max_steps=5,
            save_steps=100,
            log_steps=1,
            max_grad_norm=1.0,
            mixed_precision=False,
            checkpoint_dir=os.path.join(self.test_dir, "checkpoints"),
            log_dir=os.path.join(self.test_dir, "logs"),
            seed=42
        )
        self.model = TinyModel()
        self.dataset = DummyDataset()
        self.trainer = Trainer(self.model, self.config, self.dataset)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_causal_lm_loss(self):
        # Verify alignment: logits shift and labels shift
        # batch shape: (1, 5)
        batch = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        logits = self.model(batch)
        
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        
        # Check alignment matches expected shift
        self.assertEqual(shift_logits.shape, (1, 4, 10))
        self.assertEqual(shift_labels.shape, (1, 4))
        
        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        self.assertTrue(torch.isfinite(loss))

    def test_forward_backward_and_cpu_training(self):
        # Run a tiny step and assert parameters change
        old_params = [p.clone() for p in self.model.parameters()]
        
        # Run 1 optimizer step
        self.trainer.train()
        
        new_params = list(self.model.parameters())
        # Verify at least some parameters have updated
        updated = any(not torch.equal(o, n) for o, n in zip(old_params, new_params))
        self.assertTrue(updated)
        
        self.assertEqual(self.trainer.device.type, "cpu")

    def test_optimizer_and_scheduler_stepping(self):
        # Verify step increment
        self.assertEqual(self.trainer.optimizer_step, 0)
        self.trainer.train()
        self.assertEqual(self.trainer.optimizer_step, 5)

    def test_gradient_accumulation(self):
        # Accumulate gradients over 2 micro-steps
        self.config.gradient_accumulation_steps = 2
        self.config.max_steps = 1
        
        accum_model = TinyModel()
        accum_trainer = Trainer(accum_model, self.config, self.dataset)
        
        old_params = [p.clone() for p in accum_model.parameters()]
        
        # We manually run iterations
        data_iter = iter(self.dataset)
        accum_trainer.optimizer.zero_grad()
        
        # Step 1: micro-step = 1. No parameter updates should occur.
        batch = next(data_iter)
        logits = accum_model(batch)
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)) / 2
        loss.backward()
        accum_trainer.micro_step += 1
        
        # Verify no parameter update yet
        new_params = list(accum_model.parameters())
        self.assertTrue(all(torch.equal(o, n) for o, n in zip(old_params, new_params)))
        
        # Step 2: micro-step = 2. Update should occur.
        batch = next(data_iter)
        logits = accum_model(batch)
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)) / 2
        loss.backward()
        accum_trainer.micro_step += 1
        
        # Trigger optimizer update
        if accum_trainer.micro_step % 2 == 0:
            torch.nn.utils.clip_grad_norm_(accum_model.parameters(), accum_trainer.config.max_grad_norm)
            accum_trainer.optimizer.step()
            accum_trainer.scheduler.step()
            accum_trainer.optimizer.zero_grad()
            accum_trainer.optimizer_step += 1
            
        # Verify update happened
        new_params_after = list(accum_model.parameters())
        updated = any(not torch.equal(o, n) for o, n in zip(old_params, new_params_after))
        self.assertTrue(updated)

    def test_gradient_clipping(self):
        # Multiply loss to force very large gradients
        self.trainer.optimizer.zero_grad()
        batch = next(iter(self.dataset))
        logits = self.model(batch)
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)) * 1000.0
        loss.backward()
        
        norm_before = torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.assertGreater(norm_before, 1.0)
        
        # Re-verify that clipping kept total norm <= 1.0 + tolerance
        norm_after = torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.assertLessEqual(norm_after, 1.001)

    def test_training_config_validation(self):
        config_path = os.path.join(self.test_dir, "test_config.json")
        self.config.save(config_path)
        loaded = TrainingConfig.load(config_path)
        self.assertEqual(loaded.learning_rate, self.config.learning_rate)
        self.assertEqual(loaded.max_steps, self.config.max_steps)

    def test_tiny_overfit(self):
        # Train on a single sequence repeatedly to overfit and decrease loss
        overfit_model = TinyModel(vocab_size=5, hidden_dim=16)
        batch = torch.tensor([[0, 1, 2, 3, 4]], dtype=torch.long)
        
        class SingleBatchDataset:
            def __iter__(self):
                while True:
                    yield batch
                    
        config = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=5e-3,
            weight_decay=0.0,
            max_steps=50,
            log_steps=1,
            checkpoint_dir=os.path.join(self.test_dir, "checkpoints"),
            log_dir=os.path.join(self.test_dir, "logs")
        )
        
        overfit_trainer = Trainer(overfit_model, config, SingleBatchDataset())
        
        # Get initial loss
        logits = overfit_model(batch)
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        initial_loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)).item()
        
        # Train
        overfit_trainer.train()
        
        # Get final loss
        logits = overfit_model(batch)
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch[..., 1:].contiguous()
        final_loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)).item()
        
        print(f"Initial loss: {initial_loss:.4f}, Final loss: {final_loss:.4f}")
        self.assertLess(final_loss, initial_loss)
        self.assertTrue(np.isfinite(final_loss))

if __name__ == "__main__":
    unittest.main()
