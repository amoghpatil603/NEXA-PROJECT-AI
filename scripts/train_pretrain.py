"""
NEXA Authoritative Pretraining Entrypoint.
Wires NexaConfig.tiny() with TrainingConfig, ShardDataLoader, and Trainer.
"""

import argparse
import os
import sys
import torch
from pathlib import Path

from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer

def build_parser():
    parser = argparse.ArgumentParser(description="NEXA Model Pretraining CLI")
    parser.add_argument("--batch-size", type=int, default=8, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=3e-4, help="Peak learning rate")
    parser.add_argument("--weight-decay", type=float, default=0.1, help="Weight decay")
    parser.add_argument("--warmup-steps", type=int, default=1000, help="Warmup steps")
    parser.add_argument("--max-steps", type=int, default=100000, help="Total training steps")
    parser.add_argument("--save-steps", type=int, default=1000, help="Checkpoint interval")
    parser.add_argument("--log-steps", type=int, default=10, help="Logging interval")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/pretrain", help="Checkpoint directory")
    parser.add_argument("--log-dir", type=str, default="logs/pretrain", help="Log directory")
    parser.add_argument("--dataset-dir", type=str, default="datasets/shards", help="Binary shard dataset directory")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--dry-run", action="store_true", help="Execute single-step validation without full loop")
    return parser

def create_pretraining_setup(args=None):
    if args is None:
        args = build_parser().parse_args([])

    config = TrainingConfig(
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_steps=args.warmup_steps,
        max_steps=args.max_steps,
        save_steps=args.save_steps,
        log_steps=args.log_steps,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
        dataset_dir=args.dataset_dir,
        seed=args.seed
    )

    model_config = NexaConfig.tiny()
    model = NexaTransformer(model_config)

    # Initialize dataloader if dataset dir exists, otherwise empty placeholder for dry run
    if Path(args.dataset_dir).exists() and list(Path(args.dataset_dir).glob("*.bin")):
        dataloader = ShardDataLoader(
            shard_dir=args.dataset_dir,
            batch_size=config.batch_size,
            max_length=model_config.max_seq_len,
            shuffle=True,
            seed=config.seed
        )
    else:
        dataloader = None

    return model, config, dataloader

def main():
    parser = build_parser()
    args = parser.parse_args()

    model, config, dataloader = create_pretraining_setup(args)
    if dataloader is None:
        print(f"Error: No binary dataset shards found in '{args.dataset_dir}'.")
        sys.exit(1)

    trainer = Trainer(model, config, dataloader)
    trainer.resume_from_checkpoint()

    if args.dry_run:
        success = trainer.dry_run()
        print(f"Dry run result: {'SUCCESS' if success else 'FAILED'}")
        sys.exit(0 if success else 1)

    trainer.train()

if __name__ == "__main__":
    main()
