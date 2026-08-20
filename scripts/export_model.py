"""
NEXA Model Checkpoint Export CLI.
Exports a trained model checkpoint and its configuration to a deployment artifact directory.
"""

import argparse
import sys
from pathlib import Path
import torch

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.model.export import export_model_checkpoint

def build_parser():
    parser = argparse.ArgumentParser(description="NEXA Model Export CLI")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/pretrain/best.ckpt", help="Source checkpoint path")
    parser.add_argument("--output-dir", type=str, default="exported_model", help="Export target directory")
    parser.add_argument("--filename", type=str, default="model.pt", help="Exported weights file name")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    config = NexaConfig.tiny()
    model = NexaTransformer(config)

    if Path(args.checkpoint).exists():
        print(f"Loading checkpoint weights from {args.checkpoint}...")
        state = torch.load(args.checkpoint, map_location="cpu")
        model.load_state_dict(state.get("model_state_dict", state))

    result = export_model_checkpoint(model, config, args.output_dir, args.filename)
    print(f"Model exported successfully to {result['output_dir']} ({result['total_parameters']:,} parameters).")

if __name__ == "__main__":
    main()
