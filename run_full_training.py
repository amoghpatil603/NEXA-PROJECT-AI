import os
import sys
import json
import time
import struct
import torch
import torch.nn as nn
from pathlib import Path

# LIMIT CPU THREADS TO PREVENT HEALTHCHECK FAILURE
torch.set_num_threads(1)

sys.path.insert(0, 'nexa-model')

from training.config import TrainingConfig
from training.scheduler import get_cosine_schedule_with_warmup
from training.trainer import Trainer
from training.checkpoint import save_checkpoint, load_checkpoint
from training.utils import set_seed, get_rss_mb, get_device
from model.config import NexaConfig
from model.transformer import NexaTransformer

torch.serialization.add_safe_globals([TrainingConfig])

print("=== STARTING NEXA FULL TRAINING ===")
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

# Convergence settings
MAX_STEPS = 2000
EVAL_INTERVAL = 50
EARLY_STOP_PATIENCE = 5

train_config = TrainingConfig(
    learning_rate=3e-4,
    weight_decay=0.1,
    warmup_steps=200,
    max_steps=MAX_STEPS,
    min_lr_ratio=0.1,
    grad_clip=1.0,
    gradient_accumulation_steps=4,
    micro_batch_size=2,
    context_len=256,
    seed=42,
    output_dir="checkpoints_full",
    save_every_steps=EVAL_INTERVAL,
    log_every_steps=10,
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
    print(f"Found existing checkpoint at {latest_ckpt_path}, resuming training...")
    loaded = load_checkpoint(str(latest_ckpt_path), model, optimizer, scheduler)
    trainer.global_step = loaded.get("global_step", 0)
    start_step = trainer.global_step + 1
    best_val_loss = loaded.get("best_val_loss", float('inf'))
    print(f"Resumed from global step {trainer.global_step}")

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

# 95% train, 5% val
split_idx = int(0.95 * len(chunks))
train_chunks = chunks[:split_idx]
val_chunks = chunks[split_idx:]

print(f"Created {len(train_chunks)} train chunks and {len(val_chunks)} val chunks.")

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
            logits, loss = model(b_inputs, b_targets)
            total_loss += loss.item()
            total_batches += 1
            if total_batches >= 20: # Limit eval batches for speed
                break
            # Yield CPU to prevent healthcheck failure
            time.sleep(0.005)
    model.train()
    return total_loss / max(1, total_batches)

accumulation_loss = 0.0
steps_accumulated = 0
patience_counter = 0

print(f"Starting training from step {start_step} to {train_config.max_steps}...")
optimizer.zero_grad()

step_start_time = time.time()
tokens_per_sec = 0.0

for step in range(start_step, train_config.max_steps + 1):
    # Yield CPU periodically so control plane API doesn't starve and fail health checks!
    time.sleep(0.01)

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
    steps_accumulated += 1
    
    if is_last_micro:
        avg_loss = accumulation_loss / train_config.gradient_accumulation_steps
        current_lr = optimizer.param_groups[0]["lr"]
        g_step = trainer.global_step
        
        # Calculate tokens/sec
        step_time = time.time() - step_start_time
        step_tokens = train_config.gradient_accumulation_steps * train_config.micro_batch_size * train_config.context_len
        tokens_per_sec = step_tokens / max(0.001, step_time)
        step_start_time = time.time()

        # Compute gradient norm
        grad_norm = step_info.get("grad_norm", 0.0)
        
        current_rss = get_rss_mb()
        if current_rss > peak_rss:
            peak_rss = current_rss
            
        if g_step % train_config.log_every_steps == 0:
            print(f"Step {g_step}/{train_config.max_steps} | Loss: {avg_loss:.4f} | LR: {current_lr:.2e} | GradNorm: {grad_norm:.4f} | Tok/s: {tokens_per_sec:.1f} | RSS: {current_rss:.1f}MB")
            
        if g_step % train_config.save_every_steps == 0:
            val_loss = evaluate(model, val_dataloader)
            
            improvement = best_val_loss - val_loss
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                state_best = {
                    "global_step": g_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
                    "rng_state": torch.get_rng_state(),
                    "config": train_config,
                    "best_val_loss": best_val_loss
                }
                save_checkpoint(state_best, str(checkpoint_dir), "best.ckpt")
                patience_counter = 0
                imp_str = f"{improvement:.4f}" if improvement != float('inf') else "N/A"
                print(f"New best validation loss: {val_loss:.4f} (Improved by {imp_str}). Saved best.ckpt")
            else:
                patience_counter += 1
                print(f"Validation loss: {val_loss:.4f} (No improvement). Patience: {patience_counter}/{EARLY_STOP_PATIENCE}")
                
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
            print(f"Checkpoint saved at step {g_step} to latest.ckpt")
            
            # Generate evaluation report
            steps_left = train_config.max_steps - g_step
            avg_step_time = step_tokens / tokens_per_sec if tokens_per_sec > 0 else 0
            est_rem_time = steps_left * avg_step_time
            est_rem_str = f"{int(est_rem_time // 60)}m {int(est_rem_time % 60)}s"

            report = f"""# NEXA Training Evaluation Interval Report (Step {g_step})
- **Current Training Loss**: {avg_loss:.4f}
- **Current Validation Loss**: {val_loss:.4f}
- **Improvement from Previous Best**: {imp_str if val_loss < best_val_loss + improvement else 'N/A'}
- **Estimated Remaining Training Time**: {est_rem_str}
"""
            with open("evaluation_interval_report.md", "w") as f:
                f.write(report)
                
            if patience_counter >= EARLY_STOP_PATIENCE:
                print(f"Early stopping triggered at step {g_step}.")
                break
                
        accumulation_loss = 0.0
        steps_accumulated = 0

print("Training finished.")
