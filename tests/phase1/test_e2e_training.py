
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
    def test_optimizer_step_delta(self):
        test_dir = Path('/tmp/e2e_reverify')
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True, exist_ok=True)
        
        tokens = [(i % 100) + 1 for i in range(1000)]
        sharder = DatasetSharder(str(test_dir), shard_size=100)
        sharder.write(tokens)
        sharder.close()

        config = NexaFMConfig.tiny()
        model = NexaFMModel(config)
        model.train()

        loader = ShardDataLoader(str(test_dir), batch_size=2, max_length=16)
        
        # Target the first layer's weight for delta check
        param = next(model.parameters())
        initial_val = param.clone().detach()

        train_cfg = TrainingConfig(
            max_steps=1,
            gradient_accumulation_steps=1,
            learning_rate=10.0,
            checkpoint_dir='/tmp/e2e_ckpt',
            log_dir='/tmp/e2e_log'
        )
        trainer = Trainer(model, train_cfg, loader)
        trainer.train()

        # Verify numerical update occurred
        delta = torch.abs(param - initial_val).sum().item()
        print(f'Optimizer Parameter Delta: {delta}')
        self.assertGreater(delta, 0.0, "Model parameters did not update after optimizer step.")
