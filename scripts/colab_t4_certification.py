"""
NEXA Real T4 Memory & Resume Certification Script
Automates the exact 1-step, 2-step, checkpoint, and fresh-process resume validation on an NVIDIA Tesla T4 GPU.
"""

import os
import sys
import psutil
import tempfile
import subprocess
import numpy as np
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

def run_certification():
    print("=" * 60)
    print("NEXA — REAL T4 MEMORY + RESUME CERTIFICATION")
    print("=" * 60)

    # 1. Hardware Check
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "NONE"
    total_vram_gb = (torch.cuda.get_device_properties(0).total_memory / 1e9) if cuda_avail else 0.0
    sys_ram_gb = psutil.virtual_memory().total / 1e9

    print(f"CUDA Available: {cuda_avail}")
    print(f"GPU Name: {gpu_name}")
    print(f"Total VRAM: {total_vram_gb:.2f} GB")
    print(f"System RAM: {sys_ram_gb:.2f} GB")

    if not cuda_avail or "T4" not in gpu_name:
        print("\n[WARNING] This script is designed for an NVIDIA Tesla T4 GPU.")
        if not cuda_avail:
            print("[ERROR] CUDA is not available. Exiting.")
            sys.exit(1)

    device = torch.device("cuda")

    # 2. Model Check
    cfg = NexaConfig.tiny()
    print(f"\nModel Configuration:")
    print(f" - vocab_size: {cfg.vocab_size}")
    print(f" - max_seq_len: {cfg.max_seq_len}")
    print(f" - d_model: {cfg.d_model}")
    print(f" - n_layers: {cfg.n_layers}")
    print(f" - n_heads: {cfg.n_heads}")
    print(f" - d_ff: {cfg.d_ff}")

    model = NexaTransformer(cfg).to(device)
    params = sum(p.numel() for p in model.parameters())
    print(f" - Parameter Count: {params:,}")
    assert params == 49721856, f"Expected 49,721,856 parameters, got {params}"

    # 3. Data Check
    shards = list(Path("data/shards").glob("**/*.bin"))
    print(f"\nDataset Validation:")
    print(f" - Shard count: {len(shards)}")
    sample = shards[0]
    data = np.memmap(sample, dtype=np.uint16, mode='r')
    print(f" - Sample tokens: {len(data)}, dtype: {data.dtype}, max token: {int(np.max(data))}")
    assert np.max(data) < cfg.vocab_size, "Token ID exceeds vocab size!"

    dl = ShardDataLoader("data/shards", batch_size=1, max_length=cfg.max_seq_len, shuffle=False)
    batch = next(iter(dl))
    print(f" - Single batch shape: {list(batch.shape)}, dtype: {batch.dtype}")

    # 4. One-Step Execution
    print("\n--- STEP 1: ONE-STEP T4 TRAINING ---")
    tmp_dir1 = tempfile.mkdtemp()
    t_config1 = TrainingConfig(
        batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=3e-4,
        max_steps=1,
        save_steps=1,
        checkpoint_dir=os.path.join(tmp_dir1, "ckpts"),
        log_dir=os.path.join(tmp_dir1, "logs"),
        dataset_dir="data/shards",
        seed=42
    )
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    trainer1 = Trainer(model, t_config1, dl)
    trainer1.train()

    one_step_allocated = torch.cuda.memory_allocated(device) / 1e9
    one_step_reserved = torch.cuda.memory_reserved(device) / 1e9
    one_step_peak = torch.cuda.max_memory_allocated(device) / 1e9
    one_step_peak_pct = (one_step_peak / total_vram_gb) * 100

    print(f"One-Step Peak VRAM: {one_step_peak:.2f} GB ({one_step_peak_pct:.2f}%)")
    assert one_step_peak_pct < 70.0, f"Peak VRAM exceeded 70% limit! ({one_step_peak_pct:.2f}%)"

    # 5. Two-Step Execution
    print("\n--- STEP 2: TWO-STEP T4 TRAINING ---")
    tmp_dir2 = tempfile.mkdtemp()
    t_config2 = TrainingConfig(
        batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=3e-4,
        max_steps=2,
        save_steps=1,
        checkpoint_dir=os.path.join(tmp_dir2, "ckpts"),
        log_dir=os.path.join(tmp_dir2, "logs"),
        dataset_dir="data/shards",
        seed=42
    )
    model2 = NexaTransformer(cfg).to(device)
    dl2 = ShardDataLoader("data/shards", batch_size=1, max_length=cfg.max_seq_len, shuffle=False)

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    trainer2 = Trainer(model2, t_config2, dl2)
    trainer2.train()

    two_step_peak = torch.cuda.max_memory_allocated(device) / 1e9
    two_step_peak_pct = (two_step_peak / total_vram_gb) * 100
    print(f"Two-Step Peak VRAM: {two_step_peak:.2f} GB ({two_step_peak_pct:.2f}%)")
    assert os.path.exists(os.path.join(tmp_dir2, "ckpts", "checkpoint-1")), "checkpoint-1 missing!"
    assert os.path.exists(os.path.join(tmp_dir2, "ckpts", "checkpoint-2")), "checkpoint-2 missing!"

    # 6. Fresh-Process Resume Subprocess Execution
    print("\n--- STEP 3: FRESH-PROCESS RESUME & STEP 3 ---")
    sub_script = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{REPO_ROOT}")
import torch
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.training_engine.trainer import Trainer

cfg = NexaConfig.tiny()
model = NexaTransformer(cfg).cuda()
t_config = TrainingConfig(
    batch_size=1,
    gradient_accumulation_steps=1,
    learning_rate=3e-4,
    max_steps=3,
    save_steps=1,
    checkpoint_dir=r"{os.path.join(tmp_dir2, 'ckpts')}",
    log_dir=r"{os.path.join(tmp_dir2, 'logs')}",
    dataset_dir="data/shards",
    seed=42
)
dl = ShardDataLoader("data/shards", batch_size=1, max_length=cfg.max_seq_len, shuffle=False)
trainer = Trainer(model, t_config, dl)
resumed = trainer.resume_from_checkpoint()
if not resumed or trainer.optimizer_step != 2:
    sys.exit(1)

trainer.train()
if trainer.optimizer_step != 3:
    sys.exit(2)

print(f"RESUME_PEAK_VRAM_GB:{{torch.cuda.max_memory_allocated() / 1e9:.3f}}")
sys.exit(0)
"""
    sub_file = os.path.join(tmp_dir2, "sub_resume.py")
    with open(sub_file, "w", encoding="utf-8") as f:
        f.write(sub_script)

    res = subprocess.run([sys.executable, sub_file], capture_output=True, text=True)
    print("Process 2 stdout:\n", res.stdout)
    if res.returncode != 0:
        print("Process 2 stderr:\n", res.stderr)
        sys.exit(1)

    print("=" * 60)
    print("ALL REAL T4 MEMORY & RESUME CHECKS PASSED ✅")
    print("=" * 60)

if __name__ == "__main__":
    run_certification()
