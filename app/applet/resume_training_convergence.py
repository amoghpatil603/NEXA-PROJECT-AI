import os
import sys
import json
import time
import math
import struct
import torch
import torch.nn as nn
from pathlib import Path

sys.path.insert(0, 'nexa-model')
from training.config import TrainingConfig
from training.scheduler import get_cosine_schedule_with_warmup
from training.trainer import Trainer
from training.checkpoint import save_checkpoint, load_checkpoint
from training.utils import set_seed, get_rss_mb, get_device
from model.config import NexaConfig
from model.transformer import NexaTransformer

torch.serialization.add_safe_globals([TrainingConfig])

def run_resumed_training():
    print("=== NEXA RESUMED TRAINING FOR CONVERGENCE ===")
    start_time = time.time()
    start_rss = get_rss_mb()
    peak_rss = start_rss
    set_seed(42)
    device = get_device("cpu")

    nexa_config = NexaConfig(
        vocab_size=8000,
        max_seq_len=256,
        d_model=384,
        n_layers=6,
        n_heads=6,
        d_ff=1536,
        dropout=0.1,
        norm_eps=1e-5,
        weight_tying=True,
        bias=False
    )

    model = NexaTransformer(nexa_config).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model initialized with {n_params:,} parameters.")

    train_config = TrainingConfig(
        learning_rate=3e-4,
        weight_decay=0.1,
        warmup_steps=200,
        max_steps=2500,  # Train further towards convergence
        min_lr_ratio=0.1,
        grad_clip=1.0,
        gradient_accumulation_steps=8,
        micro_batch_size=1,
        context_len=256,
        seed=42,
        output_dir="checkpoints_phase4e",
        save_every_steps=500,
        log_every_steps=50,
        device="cpu"
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=train_config.learning_rate,
        weight_decay=train_config.weight_decay,
        betas=(train_config.beta1, train_config.beta2),
        eps=train_config.eps
    )

    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        warmup_steps=train_config.warmup_steps,
        max_steps=train_config.max_steps,
        min_lr_ratio=train_config.min_lr_ratio
    )

    trainer = Trainer(model, optimizer, scheduler, train_config)
    checkpoint_dir = Path(train_config.output_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    latest_ckpt_path = checkpoint_dir / "latest.ckpt"
    best_ckpt_path = checkpoint_dir / "best.ckpt"

    start_step = 1
    best_val_loss = float('inf')
    if latest_ckpt_path.exists():
        print(f"Resuming training from latest checkpoint: {latest_ckpt_path}")
        loaded = load_checkpoint(str(latest_ckpt_path), model, optimizer, scheduler)
        trainer.global_step = loaded.get("global_step", 0)
        start_step = trainer.global_step + 1
        best_val_loss = loaded.get("best_val_loss", loaded.get("best_loss", float('inf')))
        print(f"Resumed at global step {trainer.global_step}, best_val_loss={best_val_loss:.4f}")
    else:
        print("No existing checkpoint found. Starting training from step 1 (incorporating Phase 4e baseline).")

    # Load shards
    shard_dir = Path("data/shards/pd5m_v7_8k_recovered/train")
    shard_files = sorted(list(shard_dir.glob("*.bin")))
    all_tokens = []
    for sf in shard_files:
        data = sf.read_bytes()
        num_tokens = len(data) // 4
        if num_tokens > 0:
            tokens = list(struct.unpack(f"<{num_tokens}I", data[:num_tokens * 4]))
            tokens = [t % nexa_config.vocab_size for t in tokens]
            all_tokens.extend(tokens)
    print(f"Loaded {len(all_tokens)} tokens from {len(shard_files)} shards.")

    context_len = train_config.context_len
    chunks = []
    for i in range(0, len(all_tokens) - context_len - 1, context_len):
        chunk_input = all_tokens[i : i + context_len]
        chunk_target = all_tokens[i + 1 : i + context_len + 1]
        if len(chunk_input) == context_len and len(chunk_target) == context_len:
            chunks.append((torch.tensor(chunk_input, dtype=torch.long), torch.tensor(chunk_target, dtype=torch.long)))

    import random
    random.seed(42)
    random.shuffle(chunks)
    split_idx = int(0.95 * len(chunks))
    train_chunks = chunks[:split_idx]
    val_chunks = chunks[split_idx:]
    print(f"Train chunks: {len(train_chunks)}, Validation chunks: {len(val_chunks)}")

    class ShardDataset(torch.utils.data.Dataset):
        def __init__(self, chunks):
            self.chunks = chunks
        def __len__(self):
            return len(self.chunks)
        def __getitem__(self, idx):
            return self.chunks[idx]

    train_dataset = ShardDataset(train_chunks)
    train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=train_config.micro_batch_size, shuffle=True, num_workers=0)
    batch_iter = iter(train_dataloader)

    val_dataset = ShardDataset(val_chunks)
    val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=train_config.micro_batch_size, shuffle=False, num_workers=0)

    def evaluate(model, val_loader):
        model.eval()
        total_loss = 0.0
        total_batches = 0
        with torch.no_grad():
            for b_inputs, b_targets in val_loader:
                b_inputs = b_inputs.to(device)
                b_targets = b_targets.to(device)
                _, loss = model(b_inputs, b_targets)
                total_loss += loss.item()
                total_batches += 1
                if total_batches >= 30:  # evaluate on 30 batches for stable val loss
                    break
        model.train()
        return total_loss / max(1, total_batches)

    accumulation_loss = 0.0
    steps_accumulated = 0
    patience = 3
    patience_counter = 0
    progress_history = []

    print(f"Starting training loop from step {start_step} to {train_config.max_steps}...")
    optimizer.zero_grad()
    step_start_time = time.time()
    
    current_train_loss = 5.5
    current_grad_norm = 0.5
    current_lr = train_config.learning_rate

    for step in range(start_step, train_config.max_steps + 1):
        try:
            b_inputs, b_targets = next(batch_iter)
        except StopIteration:
            batch_iter = iter(train_dataloader)
            b_inputs, b_targets = next(batch_iter)

        b_inputs = b_inputs.to(device)
        b_targets = b_targets.to(device)

        is_last_micro = (steps_accumulated + 1 == train_config.gradient_accumulation_steps)
        accumulate = not is_last_micro

        step_info = trainer.training_step(b_inputs, b_targets, accumulate=accumulate)
        accumulation_loss += step_info.get("loss", 0.0)
        current_grad_norm = step_info.get("grad_norm", current_grad_norm)
        steps_accumulated += 1

        if is_last_micro:
            current_train_loss = accumulation_loss / train_config.gradient_accumulation_steps
            current_lr = optimizer.param_groups[0]["lr"]
            g_step = trainer.global_step
            current_rss = get_rss_mb()
            if current_rss > peak_rss:
                peak_rss = current_rss

            if g_step % train_config.log_every_steps == 0:
                print(f"Step {g_step}/{train_config.max_steps} | Train Loss: {current_train_loss:.4f} | LR: {current_lr:.2e} | GradNorm: {current_grad_norm:.4f} | RSS: {current_rss:.1f}MB")

            if g_step % train_config.save_every_steps == 0 or g_step == train_config.max_steps:
                val_loss = evaluate(model, val_dataloader)
                perplexity = math.exp(min(val_loss, 20.0))

                # Checkpoint size
                state_latest = {
                    "global_step": g_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
                    "rng_state": torch.get_rng_state(),
                    "config": train_config,
                    "best_val_loss": best_val_loss
                }
                save_checkpoint(state_latest, str(checkpoint_dir), "latest.ckpt")
                latest_size = latest_ckpt_path.stat().st_size if latest_ckpt_path.exists() else 0

                improvement = best_val_loss - val_loss
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    state_best = state_latest.copy()
                    state_best["best_val_loss"] = best_val_loss
                    save_checkpoint(state_best, str(checkpoint_dir), "best.ckpt")
                    patience_counter = 0
                    print(f"--> Step {g_step}: New Best Validation Loss: {val_loss:.4f} (PPL: {perplexity:.2f}). Saved best.ckpt")
                else:
                    patience_counter += 1
                    print(f"--> Step {g_step}: Validation Loss: {val_loss:.4f} (PPL: {perplexity:.2f}). No improvement. Patience: {patience_counter}/{patience}")

                best_size = best_ckpt_path.stat().st_size if best_ckpt_path.exists() else latest_size

                progress_history.append({
                    "step": g_step,
                    "train_loss": round(current_train_loss, 4),
                    "val_loss": round(val_loss, 4),
                    "perplexity": round(perplexity, 2),
                    "learning_rate": current_lr,
                    "grad_norm": round(current_grad_norm, 4),
                    "memory_rss_mb": round(current_rss, 1),
                    "checkpoint_size_bytes": latest_size
                })

                # Generate TRAINING_PROGRESS.md
                generate_training_progress_report(progress_history, peak_rss, train_config.max_steps, g_step)

                if patience_counter >= patience:
                    print(f"Early stopping triggered at step {g_step} due to validation loss convergence.")
                    break

            accumulation_loss = 0.0
            steps_accumulated = 0

    print("Training finished successfully.")

def generate_training_progress_report(history, peak_rss, max_steps, current_step):
    md = f"""# NEXA Transformer — Training Progress Report

## Overview
This report tracks the continuous training progression, validation loss convergence, perplexity metrics, gradient norms, learning rates, memory footprint, and checkpoint artifacts for the 13.8M parameter NEXA Transformer model.

- **Current Step / Max Steps**: {current_step} / {max_steps}
- **Peak Memory RSS**: {peak_rss:.1f} MB
- **Model Architecture**: 13.8M Parameters (6 Layers, 384 d_model, 6 Heads)
- **Status**: IN_PROGRESS / CONVERGING

---

## Checkpoint & Evaluation Log

| Step | Training Loss | Validation Loss | Perplexity (PPL) | Learning Rate | Gradient Norm | Memory RSS (MB) | Checkpoint Size (Bytes) |
|---|---|---|---|---|---|---|---|
"""
    for h in history:
        md += f"| {h['step']} | {h['train_loss']} | {h['val_loss']} | {h['perplexity']} | {h['learning_rate']:.2e} | {h['grad_norm']} | {h['memory_rss_mb']} | {h['checkpoint_size_bytes']:,} |\n"

    md += """
---
## Convergence & Early Stopping Analysis
- **Validation Loss Trend**: Monitored every 500 steps.
- **Patience Counter**: Active (Triggers after 3 non-improving evaluation intervals).
- **Artifacts Saved**: `latest.ckpt` and `best.ckpt` in `checkpoints_phase4e/`.
"""
    Path("TRAINING_PROGRESS.md").write_text(md)
    print("TRAINING_PROGRESS.md successfully generated/updated.")

if __name__ == "__main__":
    run_resumed_training()
