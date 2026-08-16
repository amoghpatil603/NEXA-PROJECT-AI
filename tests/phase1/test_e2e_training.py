
import unittest
import torch
from pathlib import Path
from backend.models.nexa_fm.data_pipeline.sharding import DatasetSharder
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.architecture import NexaFMModel
from backend.models.nexa_fm.config import NexaFMConfig
from backend.models.nexa_fm.training_engine.trainer import Trainer
from backend.models.nexa_fm.training_engine.config import TrainingConfig

class TestE2E(unittest.TestCase):
    def test_training_step_parameter_change(self):
        test_dir = Path('/tmp/e2e_test_final')
        if not test_dir.exists():
            test_dir.mkdir(parents=True, exist_ok=True)

        # Setup binary data
        tokens = [(i % 100) + 1 for i in range(1000)]
        sharder = DatasetSharder(str(test_dir), shard_size=100)
        sharder.write(tokens)
        sharder.close()

        config = NexaFMConfig.tiny()
        model = NexaFMModel(config)
        model.train()

        loader = ShardDataLoader(str(test_dir), batch_size=2, max_length=16)
        
        # Target a specific weight parameter
        param = model.layers[0].attn.q_proj.weight
        param.requires_grad = True
        
        # Snapshot initial values
        initial_param = param.clone().detach()

        # Configure Trainer
        train_cfg = TrainingConfig(
            max_steps=1,
            checkpoint_dir='/tmp/ckpt_final',
            log_dir='/tmp/logs_final',
            learning_rate=1.0  # High LR to ensure visible change
        )
        trainer = Trainer(model, train_cfg, loader)

        # Execute Step
        trainer.train()

        # Snapshot updated values
        updated_param = param.detach()

        # 1. Verify Gradients exist and are non-zero
        self.assertIsNotNone(param.grad)
        grad_norm = param.grad.abs().sum().item()
        self.assertGreater(grad_norm, 0.0, "Gradients were not generated.")

        # 2. Verify Parameter Update (Optimizer Step success)
        delta = torch.max(torch.abs(updated_param - initial_param)).item()
        print(f"Optimizer Step Delta: {delta}")
        self.assertGreater(delta, 0.0, "Optimizer failed to update model parameters.")

if __name__ == '__main__':
    unittest.main()
