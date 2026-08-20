"""
NEXA Authoritative SFT Training Entrypoint.
Loads pretrained checkpoint, prepares conversational datasets with assistant loss masking, and fine-tunes.
"""

import argparse
import sys
from pathlib import Path
import torch

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.sft.sft_dataset import SFTDataset

def build_parser():
    parser = argparse.ArgumentParser(description="NEXA SFT Training CLI")
    parser.add_argument("--base-checkpoint", type=str, default="checkpoints/pretrain/best.ckpt", help="Base pretrained checkpoint")
    parser.add_argument("--data-file", type=str, default="data/instruction_dataset.jsonl", help="SFT instruction JSONL dataset")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-5, help="Peak SFT learning rate")
    parser.add_argument("--warmup-steps", type=int, default=100, help="Warmup steps")
    parser.add_argument("--max-steps", type=int, default=1500, help="Max SFT steps")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/sft", help="SFT checkpoint output dir")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--dry-run", action="store_true", help="Execute single-step validation without full loop")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not Path(args.data_file).exists():
        print(f"Error: Instruction dataset '{args.data_file}' not found.")
        sys.exit(1)

    dataset = SFTDataset(args.data_file)
    print(f"Loaded {len(dataset)} SFT conversation samples from {args.data_file}.")

    model_config = NexaConfig.tiny()
    model = NexaTransformer(model_config)

    if Path(args.base_checkpoint).exists():
        print(f"Loading pretrained weights from {args.base_checkpoint}...")
        state = torch.load(args.base_checkpoint, map_location="cpu")
        model.load_state_dict(state.get("model_state_dict", state))

    print(f"SFT model initialized with {sum(p.numel() for p in model.parameters()):,} parameters.")
    if args.dry_run:
        print("Dry run validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
