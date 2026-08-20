import json
import torch
import os
from pathlib import Path
from typing import Dict, Any, Optional

def export_model_checkpoint(
    model: torch.nn.Module,
    config: Any,
    output_dir: str | Path,
    filename: str = "model.pt"
) -> Dict[str, Any]:
    """
    Exports a trained model state_dict along with configuration and parameter metadata manifest.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    weights_path = out_dir / filename
    config_path = out_dir / "config.json"
    manifest_path = out_dir / "manifest.json"

    # Save weights
    state_dict = model.state_dict()
    torch.save(state_dict, weights_path)

    # Save config
    if hasattr(config, "to_json"):
        config_json_str = config.to_json()
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_json_str)
    elif hasattr(config, "__dict__"):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.__dict__, f, indent=2)

    # Compute manifest metadata
    total_params = sum(p.numel() for p in model.parameters())
    num_tensors = len(state_dict)

    manifest = {
        "format": "pytorch_state_dict",
        "weights_file": filename,
        "total_parameters": total_params,
        "num_tensors": num_tensors,
        "config_file": "config.json"
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "output_dir": str(out_dir),
        "weights_path": str(weights_path),
        "config_path": str(config_path),
        "manifest_path": str(manifest_path),
        "total_parameters": total_params
    }
