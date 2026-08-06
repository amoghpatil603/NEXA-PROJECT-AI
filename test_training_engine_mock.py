import sys
from unittest.mock import MagicMock

# Mock torch before it's imported
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.optim'] = MagicMock()
sys.modules['torch.cuda'] = MagicMock()
sys.modules['torch.backends'] = MagicMock()
sys.modules['torch.autocast'] = MagicMock

# Create a mock for autocast context manager
class MockAutocast:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

import torch
torch.autocast = MockAutocast

import os
from backend.models.nexa_fm.training_engine import TrainingConfig, Trainer, CheckpointManager

class DummyModel:
    def __init__(self):
        self.parameters = lambda: []
    def to(self, device):
        pass
    def train(self):
        pass
    def state_dict(self):
        return {"dummy": "weights"}
    def load_state_dict(self, state_dict):
        pass
    def named_parameters(self):
        return []

class DummyDataLoader:
    def __init__(self):
        class DummyBatch:
            def to(self, device):
                return self
        self.data = [DummyBatch()] * 5
    def __iter__(self):
        return iter(self.data)

def test_training_engine():
    print("Testing Training Engine with mocks...")
    config = TrainingConfig(
        batch_size=8,
        max_steps=5,
        save_steps=2,
        log_steps=1,
        checkpoint_dir="test_checkpoints_mock",
        log_dir="test_logs_mock"
    )
    
    model = DummyModel()
    dataloader = DummyDataLoader()
    
    # We set optimizer to None to simulate the loop
    trainer = Trainer(model, config, dataloader)
    trainer.optimizer = None
    
    trainer.train()
    
    # Check checkpoints
    assert os.path.exists("test_checkpoints_mock")
    latest = trainer.checkpoint_manager.get_latest_checkpoint()
    assert latest is not None, "Checkpoint not saved"
    print(f"Latest checkpoint: {latest}")
    
    # Test resume
    trainer2 = Trainer(model, config, dataloader)
    trainer2.optimizer = None
    
    # Mock torch load for resume
    torch.load = lambda x, map_location: {"model_state_dict": {}, "step": 3, "epoch": 0}
    trainer2.resume_from_checkpoint()
    assert trainer2.global_step == 3, "Resume failed"
    
    print("Training Engine validation passed.")

if __name__ == "__main__":
    test_training_engine()
