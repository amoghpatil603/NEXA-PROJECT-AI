# NEXA Pretraining Restart-Safe Checkpoint Runbook

This document details the persistent checkpoint architecture, cross-session recovery protocol, and execution guide for pretraining the **NEXA Tiny Foundation Model** across Google Colab T4 runtime terminations.

---

## 1. Overview & Architectural Guarantees

NEXA foundation pretraining is designed to survive arbitrary Colab session timeouts, GPU preemptions, and runtime disconnections without loss of training progress.

### Core Guarantees:
1. **Atomic Checkpoint Writes**: Checkpoints are written to isolated temporary directories (`.tmp_checkpoint_{step}_{uuid}`) and atomically promoted (`os.rename`) to `checkpoint-{step}` only upon complete disk flush.
2. **Automatic Latest Discovery**: The `CheckpointManager` parses checkpoint directories numerically (`checkpoint-1000` > `checkpoint-200`), verifies integrity, skips partial/temporary writes, and automatically selects the highest valid step.
3. **Corrupt Checkpoint Fallback**: If the latest checkpoint is truncated or corrupted (e.g., due to sudden VM power cutoff mid-promotion), `CheckpointManager` logs a warning and safely rolls back to the previous intact checkpoint.
4. **Complete State Restoration**: Resumes model weights, AdamW optimizer states, LR scheduler step, AMP GradScaler state, Python/NumPy/PyTorch RNG states, and exact memory-mapped DataLoader cursor positions.
5. **Strict Identity Integrity Guards**: On resume, the training engine validates that `dataset_version`, `dataset_content_hash`, `tokenizer_identity`, and `tokenizer_config_identity` match the original training run.

---

## 2. Multi-Session Colab T4 Workflow

### Session 1: Initial Training Run

```python
# 1. Mount Persistent Google Drive Storage
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone or Update NEXA Repository
!git clone https://github.com/amoghpatil603/NEXA-PROJECT-AI.git
%cd NEXA-PROJECT-AI
!git checkout main
!pip install -r requirements.txt pytest

# 3. Define Persistent External Checkpoint Directory
CHECKPOINT_DIR = "/content/drive/MyDrive/NEXA/checkpoints/pretrain"

# 4. Launch Pretraining (Checkpoints written to Google Drive every 500 steps)
!python scripts/train_pretrain.py \
    --batch-size 8 \
    --grad-accum 4 \
    --lr 3e-4 \
    --weight-decay 0.1 \
    --warmup-steps 1000 \
    --max-steps 100000 \
    --save-steps 500 \
    --log-steps 10 \
    --dataset-dir data/shards \
    --checkpoint-dir /content/drive/MyDrive/NEXA/checkpoints/pretrain \
    --log-dir /content/drive/MyDrive/NEXA/logs/pretrain \
    --seed 42
```

---

### Session Interruption & Termination
*Google Colab runtime disconnects or reaches maximum session duration (12h).*

---

### Session 2 (and subsequent sessions): Automatic Resume

```python
# 1. Reconnect Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone or Pull Latest Code
!git clone https://github.com/amoghpatil603/NEXA-PROJECT-AI.git
%cd NEXA-PROJECT-AI
!git checkout main
!pip install -r requirements.txt pytest

# 3. Run Pretraining with SAME Persistent Checkpoint Directory
# The Trainer automatically discovers the highest valid checkpoint on Google Drive and resumes seamlessly.
!python scripts/train_pretrain.py \
    --batch-size 8 \
    --grad-accum 4 \
    --lr 3e-4 \
    --weight-decay 0.1 \
    --warmup-steps 1000 \
    --max-steps 100000 \
    --save-steps 500 \
    --log-steps 10 \
    --dataset-dir data/shards \
    --checkpoint-dir /content/drive/MyDrive/NEXA/checkpoints/pretrain \
    --log-dir /content/drive/MyDrive/NEXA/logs/pretrain \
    --seed 42
```

---

## 3. Checkpoint Interval Configuration

You can tune `--save-steps` based on I/O bandwidth and progress risk tolerance:

| `--save-steps` | Progress Risk at Disconnect | Drive I/O Overhead | Recommended Use |
|---|---|---|---|
| `250` | ~8-12 minutes | Moderate | Preemptible / spot environments |
| `500` | ~15-25 minutes | Low | Standard Google Colab Free / Pro (Recommended) |
| `1000` | ~30-50 minutes | Minimal | Dedicated High-Availability GPUs |

---

## 4. Troubleshooting & Operational Procedures

### A. How to Recover from a Corrupted Checkpoint
The system automatically ignores corrupted checkpoints and resumes from the latest intact one. To manually inspect or remove corrupted states:
```bash
# Check contents of checkpoint directory
ls -la /content/drive/MyDrive/NEXA/checkpoints/pretrain/

# Delete an incomplete or corrupted step folder if needed
rm -rf /content/drive/MyDrive/NEXA/checkpoints/pretrain/checkpoint-12500/
```

### B. How to Intentionally Start a Fresh Run
To restart pretraining from step 0 (ignoring existing checkpoints):
- Point `--checkpoint-dir` to a new directory (e.g. `/content/drive/MyDrive/NEXA/checkpoints/pretrain_v2`), OR
- Clear the existing checkpoint folder.
