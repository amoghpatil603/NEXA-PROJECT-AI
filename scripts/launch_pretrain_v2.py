"""
NEXA V2 Clean Production Pretraining Launcher
Lineage: NEXA-1-TINY-PRETRAIN-V2
Authoritative 49.72M parameter Tiny Foundation Model.
"""

import os
import sys
import psutil
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer
from backend.models.nexa_fm.training_engine.checkpoints import CheckpointManager

EXPECTED_PARAMS = 49721856

def parse_args():
    parser = argparse.ArgumentParser(description="NEXA-1-TINY-PRETRAIN-V2 Production Launcher")
    parser.add_argument("--checkpoint-dir", type=str, default="/content/drive/MyDrive/NEXA/checkpoints/pretrain_v2", help="V2 checkpoint directory")
    parser.add_argument("--log-dir", type=str, default="/content/drive/MyDrive/NEXA/logs/pretrain_v2", help="V2 log directory")
    parser.add_argument("--run-metadata-dir", type=str, default="/content/drive/MyDrive/NEXA/run_metadata/pretrain_v2", help="V2 metadata directory")
    parser.add_argument("--dataset-dir", type=str, default="data/shards", help="Authoritative binary shard dataset directory")
    parser.add_argument("--batch-size", type=int, default=1, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=32, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=3e-4, help="Peak learning rate")
    parser.add_argument("--weight-decay", type=float, default=0.1, help="Weight decay")
    parser.add_argument("--warmup-steps", type=int, default=1000, help="Warmup steps")
    parser.add_argument("--max-steps", type=int, default=100000, help="Total training steps")
    parser.add_argument("--save-steps", type=int, default=500, help="Periodic save steps")
    parser.add_argument("--early-save-steps", type=str, default="1,10,50,100", help="Early checkpoint steps")
    parser.add_argument("--log-steps", type=int, default=10, help="Logging step interval")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--allow-cpu-smoke", action="store_true", help="Allow CPU execution for smoke testing only")
    return parser.parse_args()

def check_process_exclusivity(metadata_dir: str):
    os.makedirs(metadata_dir, exist_ok=True)
    pid_file = os.path.join(metadata_dir, "pretrain_v2.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if proc.is_running() and any("pretrain" in c.lower() for c in proc.cmdline()):
                    print(f"[PRE-FLIGHT ERROR] Active pretraining process detected with PID {old_pid}.")
                    print("Refusing to start duplicate process.")
                    sys.exit(1)
        except Exception:
            pass
    # Write current PID
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

def main():
    args = parse_args()
    print("=" * 70)
    print("NEXA V2 — CLEAN PRODUCTION PRETRAINING LAUNCH")
    print("Lineage: NEXA-1-TINY-PRETRAIN-V2")
    print("=" * 70)

    # 1. Verify V2 Checkpoint Directory Isolation (Never touch or resume V1)
    os.makedirs(args.checkpoint_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)
    os.makedirs(args.run_metadata_dir, exist_ok=True)

    ckpt_mgr = CheckpointManager(args.checkpoint_dir)
    latest_existing = ckpt_mgr.get_latest_checkpoint()
    if latest_existing is not None:
        print(f"[PRE-FLIGHT WARNING] Existing checkpoint found in V2 directory: {latest_existing}")
        print("Note: If starting a fresh V2 foundation run, clear or move existing checkpoints first.")
    else:
        print(f"[PRE-FLIGHT 1] V2 Checkpoint directory is clean and isolated: {args.checkpoint_dir}")

    # 2. Check Process Exclusivity
    check_process_exclusivity(args.run_metadata_dir)
    current_pid = os.getpid()
    print(f"[PRE-FLIGHT 2] Process lock acquired. Running PID: {current_pid}")

    # 3. Hardware Check (CUDA & GPU)
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    total_vram_gb = (torch.cuda.get_device_properties(0).total_memory / 1e9) if cuda_avail else 0.0

    print(f"[PRE-FLIGHT 3] Hardware: {gpu_name} (Total VRAM: {total_vram_gb:.2f} GB)")
    if not cuda_avail and not args.allow_cpu_smoke:
        print("[PRE-FLIGHT ERROR] CUDA is unavailable. Production pretraining requires CUDA (Tesla T4).")
        sys.exit(1)

    # 4. Instantiate and Verify Authoritative NexaConfig.tiny()
    cfg = NexaConfig.tiny()
    model = NexaTransformer(cfg)
    total_params = sum(p.numel() for p in model.parameters())

    print(f"[PRE-FLIGHT 4] Model Parameters: {total_params:,} (Expected: {EXPECTED_PARAMS:,})")
    if total_params != EXPECTED_PARAMS:
        print(f"[PRE-FLIGHT ERROR] Parameter count mismatch: {total_params} != {EXPECTED_PARAMS}")
        sys.exit(1)

    # 5. Dataset and Tokenizer Identity Verification
    early_saves = [int(s.strip()) for s in args.early_save_steps.split(",") if s.strip().isdigit()]
    try:
        t_config = TrainingConfig(
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            weight_decay=args.weight_decay,
            warmup_steps=args.warmup_steps,
            max_steps=args.max_steps,
            save_steps=args.save_steps,
            early_save_steps=early_saves,
            log_steps=args.log_steps,
            checkpoint_dir=args.checkpoint_dir,
            log_dir=args.log_dir,
            dataset_dir=args.dataset_dir,
            seed=args.seed
        )
    except Exception as e:
        print(f"[PRE-FLIGHT ERROR] TrainingConfig validation failed: {e}")
        sys.exit(1)

    print(f"[PRE-FLIGHT 5] Dataset Version: {t_config.dataset_version}")
    print(f"               Dataset Hash:    {t_config.dataset_content_hash[:16]}...")
    print(f"               Tokenizer Hash:  {t_config.tokenizer_identity[:16]}...")

    # 6. Initialize DataLoader
    dataloader = ShardDataLoader(
        shard_dir=args.dataset_dir,
        batch_size=t_config.batch_size,
        max_length=cfg.max_seq_len,
        shuffle=True,
        seed=t_config.seed
    )
    print(f"[PRE-FLIGHT 6] DataLoader initialized from '{args.dataset_dir}' with {len(dataloader.shards)} shards.")

    # 7. Initialize Trainer from SCRATCH (Do not load V1)
    # Maintain production max_steps to ensure correct scheduler construction.
    trainer = Trainer(model, t_config, dataloader)
    print(f"[PRE-FLIGHT 7] Initialized fresh Trainer. Initial optimizer_step = {trainer.optimizer_step}")
    if trainer.optimizer_step != 0:
        print(f"[PRE-FLIGHT ERROR] Fresh trainer did not start at step 0!")
        sys.exit(1)

    # 8. Complete Optimizer Step 1 and Save Checkpoint-1
    print("\nExecuting Optimizer Step 1 (effective batch size 32)...")
    trainer.train(max_steps_override=1)

    if trainer.optimizer_step != 1:
        print(f"[FATAL ERROR] Step 1 did not complete cleanly (current step: {trainer.optimizer_step})!")
        sys.exit(1)

    # 9. Verify Checkpoint-1 Structure & Persistence
    step1_dir = os.path.join(args.checkpoint_dir, "checkpoint-1")
    is_valid = trainer.checkpoint_manager.is_checkpoint_valid(step1_dir)
    if not is_valid:
        print(f"[FATAL ERROR] Checkpoint-1 at '{step1_dir}' is invalid or unreadable!")
        sys.exit(1)

    # Checkpoint content load test on CPU
    state_file = os.path.join(step1_dir, "training_state.pt")
    ckpt_content = torch.load(state_file, map_location="cpu", weights_only=False)
    required_keys = [
        'model_state_dict', 'optimizer_state_dict', 'scheduler_state_dict',
        'step', 'micro_step', 'epoch', 'rng_states', 'dataloader_state',
        'scaler_state', 'seed', 'dataset_version', 'dataset_content_hash',
        'tokenizer_identity', 'tokenizer_config_identity'
    ]
    for k in required_keys:
        if k not in ckpt_content:
            print(f"[FATAL ERROR] Checkpoint-1 is missing required key '{k}'!")
            sys.exit(1)

    # Verify resume capability from checkpoint-1
    resumed = trainer.resume_from_checkpoint(step1_dir)
    if not resumed or trainer.optimizer_step != 1:
        print(f"[FATAL ERROR] Failed to resume cleanly from checkpoint-1!")
        sys.exit(1)

    # VRAM measurements
    used_vram_gb = (torch.cuda.memory_allocated(0) / 1e9) if cuda_avail else 0.0
    vram_safe = (used_vram_gb < 0.70 * total_vram_gb) if cuda_avail else True

    # 10. Emit Required Initial Certification Report
    print("\n" + "=" * 70)
    print("V2 STATUS:\nRUNNING\n")
    print(f"MODEL PARAMS:\n{total_params:,}\n")
    print("START STEP:\n0\n")
    print("CURRENT STEP:\n1\n")
    print("CHECKPOINT-1:\nVALID\n")
    print(f"CHECKPOINT PATH:\n{step1_dir}/\n")
    print("CHECKPOINT PERSISTENCE:\nPASS\n")
    print(f"GPU:\n{gpu_name}\n")
    print(f"VRAM:\n{used_vram_gb:.2f} GB / {total_vram_gb:.2f} GB\n")
    print(f"VRAM SAFETY:\n{'PASS' if vram_safe else 'FAIL'}\n")
    print("DATASET IDENTITY:\nPASS\n")
    print("TOKENIZER IDENTITY:\nPASS\n")
    print(f"TRAINING PROCESS:\n{current_pid}")
    print("=" * 70 + "\n")

    # 11. Continue training normally toward max_steps
    print("[NEXA V2] Checkpoint-1 validated successfully. Continuing production pretraining...")
    trainer.train()

if __name__ == "__main__":
    main()
