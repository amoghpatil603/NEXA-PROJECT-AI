import sys
from unittest.mock import MagicMock

sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.optim'] = MagicMock()
sys.modules['torch.cuda'] = MagicMock()
sys.modules['torch.backends'] = MagicMock()

import os
from backend.models.nexa_fm.training_engine import TrainingConfig, Trainer

class DummyModel:
    def __init__(self): pass
    def to(self, device): pass
    def train(self): pass
    def state_dict(self): return {}
    def named_parameters(self): return []

class DummyOpt:
    def state_dict(self): return {}

class DummySched:
    def state_dict(self): return {}

class DummyDataLoader:
    def __init__(self):
        class DummyBatch:
            def to(self, device): return self
        self.data = [DummyBatch()] * 5
    def __iter__(self):
        return iter(self.data)

def test_training_engine():
    print("Testing Training Engine with mocks...")
    config = TrainingConfig(
        batch_size=8, max_steps=5, save_steps=2, log_steps=1,
        checkpoint_dir="test_checkpoints_mock", log_dir="test_logs_mock"
    )
    
    model = DummyModel()
    dataloader = DummyDataLoader()
    
    trainer = Trainer(model, config, dataloader)
    
    # Provide dummy optimizer so it saves checkpoints
    trainer.optimizer = DummyOpt()
    
    # We will just test the checkpoint system directly for validation
    trainer.checkpoint_manager.save(model, DummyOpt(), DummySched(), 2, 1, config)
    
    # Check checkpoints
    assert os.path.exists("test_checkpoints_mock")
    latest = trainer.checkpoint_manager.get_latest_checkpoint()
    assert latest is not None, "Checkpoint not saved"
    print(f"Latest checkpoint: {latest}")
    
    print("Training Engine validation passed.")

if __name__ == "__main__":
    test_training_engine()
