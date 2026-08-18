import unittest
import torch
import shutil
from pathlib import Path
from backend.models.nexa_fm.data_pipeline.sharding import DatasetSharder
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.architecture import NexaFMModel
from backend.models.nexa_fm.config import NexaFMConfig
from backend.models.nexa_fm.training_engine.trainer import Trainer
from backend.models.nexa_fm.training_engine.config import TrainingConfig

class TestE2E(unittest.TestCase):
    def setUp(self):
        # Always create temporary directories inside the workspace
        self.workspace_tmp = Path(__file__).resolve().parent.parent.parent / "tmp_test_e2e"
        if self.workspace_tmp.exists():
            shutil.rmtree(self.workspace_tmp)
        self.workspace_tmp.mkdir(parents=True, exist_ok=True)
        
        self.shard_dir = self.workspace_tmp / "shards"
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        
        self.ckpt_dir = self.workspace_tmp / "checkpoints"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_dir = self.workspace_tmp / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Generate dummy shards
        tokens = [(i % 100) + 1 for i in range(1000)]
        sharder = DatasetSharder(str(self.shard_dir), shard_size=100)
        sharder.write(tokens)
        sharder.close()

    def tearDown(self):
        if self.workspace_tmp.exists():
            shutil.rmtree(self.workspace_tmp)

    def test_optimizer_step_delta(self):
        config = NexaFMConfig.tiny()
        model = NexaFMModel(config)
        model.train()

        loader = ShardDataLoader(str(self.shard_dir), batch_size=2, max_length=16)

        param = next(model.parameters())
        initial_val = param.clone().detach()

        train_cfg = TrainingConfig(
            max_steps=5,
            gradient_accumulation_steps=1,
            learning_rate=10.0,
            checkpoint_dir=str(self.ckpt_dir),
            log_dir=str(self.log_dir)
        )
        trainer = Trainer(model, train_cfg, loader)
        trainer.train()

        delta = torch.abs(param - initial_val).sum().item()
        self.assertGreater(delta, 0.0, "Model parameters did not update numerically.")

    def test_checkpoint_resume_determinism(self):
        torch.manual_seed(42)
        
        # 1. RUN A: Train continuously for 6 steps
        config_a = NexaFMConfig.tiny()
        model_a = NexaFMModel(config_a)
        loader_a = ShardDataLoader(str(self.shard_dir), batch_size=2, max_length=16, shuffle=False)
        train_cfg_a = TrainingConfig(
            max_steps=6,
            gradient_accumulation_steps=1,
            learning_rate=1.0,
            checkpoint_dir=str(self.ckpt_dir / "run_a"),
            log_dir=str(self.log_dir / "run_a"),
            save_steps=3
        )
        trainer_a = Trainer(model_a, train_cfg_a, loader_a)
        trainer_a.train()
        
        # Save final state for comparison
        params_a = [p.clone().detach() for p in model_a.parameters()]
        
        # 2. RUN B: Train for 3 steps, save checkpoint, reload and resume to 6 steps
        torch.manual_seed(42)
        config_b = NexaFMConfig.tiny()
        model_b = NexaFMModel(config_b)
        loader_b = ShardDataLoader(str(self.shard_dir), batch_size=2, max_length=16, shuffle=False)
        
        train_cfg_b = TrainingConfig(
            max_steps=3,  # stop at 3 first
            gradient_accumulation_steps=1,
            learning_rate=1.0,
            checkpoint_dir=str(self.ckpt_dir / "run_b"),
            log_dir=str(self.log_dir / "run_b"),
            save_steps=3
        )
        trainer_b = Trainer(model_b, train_cfg_b, loader_b)
        trainer_b.train()
        
        # Now recreate and resume
        config_resumed = NexaFMConfig.tiny()
        model_resumed = NexaFMModel(config_resumed)
        loader_resumed = ShardDataLoader(str(self.shard_dir), batch_size=2, max_length=16, shuffle=False)
        
        train_cfg_resumed = TrainingConfig(
            max_steps=6,  # continue to 6
            gradient_accumulation_steps=1,
            learning_rate=1.0,
            checkpoint_dir=str(self.ckpt_dir / "run_b"),
            log_dir=str(self.log_dir / "run_b_resumed"),
            save_steps=3
        )
        
        trainer_resumed = Trainer(model_resumed, train_cfg_resumed, loader_resumed)
        trainer_resumed.resume_from_checkpoint()
        self.assertEqual(trainer_resumed.optimizer_step, 3, "Resumed optimizer step is incorrect")
        
        trainer_resumed.train()
        
        # Compare weights of model_a and model_resumed
        params_resumed = [p.clone().detach() for p in model_resumed.parameters()]
        
        for pa, pr in zip(params_a, params_resumed):
            diff = torch.abs(pa - pr).max().item()
            self.assertLess(diff, 1e-6, f"Divergence detected in resumed parameters: max diff={diff}")

if __name__ == "__main__":
    unittest.main()
