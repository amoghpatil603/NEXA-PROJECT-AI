import os
import torch
from backend.models.nexa_fm.training_engine import TrainingConfig, Trainer, CheckpointManager

class DummyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layer = torch.nn.Linear(10, 10)
        
    def forward(self, input_ids):
        # returns dummy loss
        loss = self.layer(input_ids.float()).sum()
        class Output:
            pass
        out = Output()
        out.loss = loss
        return out

class DummyDataLoader:
    def __init__(self):
        self.data = [torch.randn(8, 10)] * 10
    def __iter__(self):
        return iter(self.data)

def test_training_engine():
    print("Testing Training Engine...")
    config = TrainingConfig(
        batch_size=8,
        gradient_accumulation_steps=1,
        max_steps=5,
        save_steps=2,
        log_steps=1,
        checkpoint_dir="test_checkpoints",
        log_dir="test_logs"
    )
    
    model = DummyModel()
    dataloader = DummyDataLoader()
    
    trainer = Trainer(model, config, dataloader)
    print(f"Detected device: {trainer.device}")
    
    trainer.train()
    
    # Check checkpoints
    assert os.path.exists("test_checkpoints")
    latest = trainer.checkpoint_manager.get_latest_checkpoint()
    assert latest is not None, "Checkpoint not saved"
    print(f"Latest checkpoint: {latest}")
    
    # Test resume
    trainer2 = Trainer(model, config, dataloader)
    trainer2.resume_from_checkpoint()
    assert trainer2.global_step > 0, "Resume failed"
    
    print("Training Engine validation passed.")

if __name__ == "__main__":
    test_training_engine()
