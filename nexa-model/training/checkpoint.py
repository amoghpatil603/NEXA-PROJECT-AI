import os
import torch
from pathlib import Path

def save_checkpoint(state_dict: dict, checkpoint_dir: str, filename: str = "checkpoint_latest.pt"):
    """
    Saves training checkpoint safely.
    """
    path = Path(checkpoint_dir)
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / filename
    torch.save(state_dict, filepath)
    return str(filepath)

def load_checkpoint(filepath: str, model, optimizer=None, scheduler=None):
    """
    Loads training checkpoint into model, optimizer, and scheduler.
    Returns state dictionary containing step, epoch, etc.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Checkpoint not found at {filepath}")
        
    checkpoint = torch.load(filepath, map_location="cpu")
    
    model.load_state_dict(checkpoint["model_state_dict"])
    
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
    if scheduler is not None and "scheduler_state_dict" in checkpoint:
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        
    if "rng_state" in checkpoint:
        torch.set_rng_state(checkpoint["rng_state"])
        if torch.cuda.is_available() and "cuda_rng_state" in checkpoint:
            torch.cuda.set_rng_state_all(checkpoint["cuda_rng_state"])
            
    return checkpoint
