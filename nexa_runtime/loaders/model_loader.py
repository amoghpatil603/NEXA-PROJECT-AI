import torch
import os
from pathlib import Path

class ModelLoader:
    """Handles checkpoint discovery, validation, and loading."""
    def __init__(self, checkpoint_dir="/content/drive/MyDrive/NEXA/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.loaded_model = None
        self.current_version = None

    def discover_latest(self):
        ckpts = list(self.checkpoint_dir.glob("**/*.pth"))
        if not ckpts:
            return None
        return max(ckpts, key=os.path.getctime)

    def validate_checkpoint(self, path):
        if not path or not path.exists():
            return False
        try:
            # Minimal header check
            _ = torch.load(path, map_location="cpu", weights_only=True)
            return True
        except Exception:
            return False

    def load(self, model_class, config):
        path = self.discover_latest()
        if not self.validate_checkpoint(path):
            raise FileNotFoundError("No valid checkpoint found for loading.")

        model = model_class(config)
        state = torch.load(path, map_location="cpu")
        model.load_state_dict(state.get('model_state_dict', state))
        self.loaded_model = model
        return model

    def unload(self):
        if self.loaded_model:
            del self.loaded_model
        self.loaded_model = None
        torch.cuda.empty_cache()
