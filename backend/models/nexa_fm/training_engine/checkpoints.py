import os
try:
    import torch
except ImportError:
    torch = None
from .config import TrainingConfig
import json

class CheckpointManager:
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save(self, model, optimizer, scheduler, step: int, epoch: int, config: TrainingConfig):
        # We don't save if torch is not actually generating real models
        if optimizer is None: return
        
        path = os.path.join(self.checkpoint_dir, f"checkpoint-{step}")
        os.makedirs(path, exist_ok=True)
        
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'step': step,
            'epoch': epoch
        }, os.path.join(path, "training_state.pt"))
        
        config.save(os.path.join(path, "training_config.json"))
        
    def load(self, path: str, model, optimizer=None, scheduler=None):
        if not os.path.exists(path):
            return 0, 0
            
        state_path = os.path.join(path, "training_state.pt")
        if not os.path.exists(state_path):
            return 0, 0
            
        checkpoint = torch.load(state_path, map_location="cpu")
        model.load_state_dict(checkpoint['model_state_dict'])
        if optimizer:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if scheduler:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            
        return checkpoint.get('step', 0), checkpoint.get('epoch', 0)
        
    def get_latest_checkpoint(self):
        checkpoints = [d for d in os.listdir(self.checkpoint_dir) if d.startswith("checkpoint-")]
        if not checkpoints:
            return None
        checkpoints.sort(key=lambda x: int(x.split("-")[1]))
        return os.path.join(self.checkpoint_dir, checkpoints[-1])
