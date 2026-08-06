import os
import json
import torch
import time
from pathlib import Path
from typing import Optional, Dict, Any

def save_checkpoint(
    state_dict: Dict[str, Any],
    checkpoint_dir: str | Path,
    filename: str = "latest.ckpt",
    keep_last_n: int = 3
) -> str:
    """
    Saves training checkpoint safely along with a JSON sidecar metadata file.
    Also handles rotation of step-based checkpoints if keep_last_n > 0.
    """
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    filepath = checkpoint_path / filename
    torch.save(state_dict, filepath)
    
    # Generate sidecar JSON metadata
    sidecar_name = filepath.stem + ".json"
    sidecar_path = checkpoint_path / sidecar_name
    
    metadata = {
        "filename": filename,
        "global_step": state_dict.get("global_step", 0),
        "best_val_loss": state_dict.get("best_val_loss", None),
        "val_loss": state_dict.get("val_loss", None),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tokenizer_version": getattr(state_dict.get("config", None), "tokenizer_version", "1.0.0")
    }
    
    # Include config if serializable
    if "config" in state_dict:
        cfg = state_dict["config"]
        if hasattr(cfg, "to_dict"):
            metadata["config"] = cfg.to_dict()
        elif isinstance(cfg, dict):
            metadata["config"] = cfg

    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    # Handle checkpoint rotation for step checkpoints (e.g. ckpt_step_*.ckpt)
    if keep_last_n > 0 and filename.startswith("ckpt_step_"):
        step_ckpts = sorted(list(checkpoint_path.glob("ckpt_step_*.ckpt")) + list(checkpoint_path.glob("ckpt_step_*.pt")))
        if len(step_ckpts) > keep_last_n:
            to_remove = step_ckpts[:-keep_last_n]
            for old_ckpt in to_remove:
                try:
                    old_ckpt.unlink(missing_ok=True)
                    old_json = old_ckpt.with_suffix(".json")
                    if old_json.exists():
                        old_json.unlink(missing_ok=True)
                except Exception:
                    pass

    return str(filepath)


def load_checkpoint(
    filepath: str | Path,
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[Any] = None,
    scaler: Optional[Any] = None,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Loads training checkpoint into model, optimizer, scheduler, and scaler.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {filepath}")
        
    map_location = torch.device(device)
    checkpoint = torch.load(path, map_location=map_location)
    
    model.load_state_dict(checkpoint["model_state_dict"])
    
    if optimizer is not None and "optimizer_state_dict" in checkpoint and checkpoint["optimizer_state_dict"] is not None:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
    if scheduler is not None and "scheduler_state_dict" in checkpoint and checkpoint["scheduler_state_dict"] is not None:
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        
    if scaler is not None and "scaler_state_dict" in checkpoint and checkpoint["scaler_state_dict"] is not None:
        scaler.load_state_dict(checkpoint["scaler_state_dict"])
        
    if "rng_state" in checkpoint and checkpoint["rng_state"] is not None:
        torch.set_rng_state(checkpoint["rng_state"])
        if torch.cuda.is_available() and "cuda_rng_state" in checkpoint and checkpoint["cuda_rng_state"] is not None:
            torch.cuda.set_rng_state_all(checkpoint["cuda_rng_state"])
            
    return checkpoint
