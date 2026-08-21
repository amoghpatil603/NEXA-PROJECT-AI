# NEXA — Google Colab Tesla T4 Execution Runbook

This document is the standard operating procedure for executing certification, pretraining, and recovery on an NVIDIA Tesla T4 GPU in Google Colab.

---

## 1. Fresh Colab Environment Setup

In a new Colab notebook with runtime set to **T4 GPU**:

```python
# Check NVIDIA GPU hardware
!nvidia-smi

# Clone NEXA repository
!git clone https://github.com/amoghpatil603/NEXA-PROJECT-AI.git
%cd NEXA-PROJECT-AI

# Install dependencies
!pip install -q torch numpy psutil pytest
```

---

## 2. Google Drive Mounting (Persistent Storage)

Persisting dataset and checkpoints to Google Drive prevents data loss on runtime disconnection or timeout:

```python
from google.colab import drive
drive.mount('/content/drive')

# Establish persistent directories on Drive
import os
os.makedirs('/content/drive/MyDrive/nexa/shards', exist_ok=True)
os.makedirs('/content/drive/MyDrive/nexa/checkpoints/pretrain', exist_ok=True)
os.makedirs('/content/drive/MyDrive/nexa/logs/pretrain', exist_ok=True)
```

---

## 3. Dataset Path & Structure

The binary pretraining dataset consists of uint16 memmap binary shards (`*.bin`).

- **External Persistent Path**: `/content/drive/MyDrive/nexa/shards`
- **Supported Directory Layouts**:
  - Flat: `/content/drive/MyDrive/nexa/shards/*.bin`
  - Nested: `/content/drive/MyDrive/nexa/shards/train/*.bin`, `/content/drive/MyDrive/nexa/shards/validation/*.bin`, `/content/drive/MyDrive/nexa/shards/test/*.bin`

---

## 4. Dataset Identity Verification

Verify that the dataset matches the authoritative manifest and 8k vocabulary contract:

```bash
python -c "
from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.tokenizer.canonical_resolver import get_authoritative_tokenizer_metadata
meta = get_authoritative_tokenizer_metadata()
print('Authoritative Vocab Size:', meta['vocabulary_size'])
loader = ShardDataLoader('/content/drive/MyDrive/nexa/shards', batch_size=1)
print(f'Found {len(loader.shards)} shards.')
"
```

---

## 5. Checkpoint Path

Set persistent checkpoint output to Google Drive:
`--checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/pretrain`

---

## 6. Automated T4 Hardware & Memory Certification

Run the automated certification script to verify hardware, parameter count (49,721,856), peak VRAM (< 70%), and restart-safe resume with exact tensor equality:

```bash
python scripts/colab_t4_certification.py --dataset-dir /content/drive/MyDrive/nexa/shards --batch-size 1
```

**Success Criteria**:
- GPU detected: NVIDIA Tesla T4 (15.0 GB VRAM)
- Model Parameters: 49,721,856
- 1-Step and 2-Step Peak VRAM < 70% of 15.0 GB (< 10.5 GB)
- Subprocess Fresh-Process Resume: Step 3 executed, next-batch tensor exactly identical to uninterrupted reference batch.

---

## 7. Safe Batch-Size Selection & VRAM Ceiling Guard

The NEXA pretraining engine enforces a strict **70% VRAM ceiling** (10.5 GB on a 15 GB T4).

- **Recommended Baseline**: `--batch-size 8 --grad-accum 4` (effective batch size = 32 sequences of 2048 tokens).
- **Conservative Fallback**: `--batch-size 4 --grad-accum 8` (if memory headroom is tight).

---

## 8. 100k Pretraining Command

```bash
python scripts/train_pretrain.py \
  --dataset-dir /content/drive/MyDrive/nexa/shards \
  --checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/pretrain \
  --log-dir /content/drive/MyDrive/nexa/logs/pretrain \
  --batch-size 8 \
  --grad-accum 4 \
  --lr 3e-4 \
  --weight-decay 0.1 \
  --warmup-steps 1000 \
  --max-steps 100000 \
  --save-steps 1000 \
  --log-steps 10 \
  --seed 42
```

---

## 9. Session Disconnection & Automatic Resume

When a Colab session disconnects or reaches max duration:

### Next Session:
1. Mount Google Drive (`drive.mount('/content/drive')`).
2. Clone repository & install dependencies.
3. Re-run the exact same pretraining command:
   ```bash
   python scripts/train_pretrain.py \
     --dataset-dir /content/drive/MyDrive/nexa/shards \
     --checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/pretrain \
     --log-dir /content/drive/MyDrive/nexa/logs/pretrain \
     --batch-size 8 \
     --grad-accum 4 \
     --max-steps 100000
   ```
4. `CheckpointManager` automatically discovers the highest numbered valid checkpoint (`checkpoint-K`), restores model weights, optimizer state, learning rate schedule, AMP scaler, dataloader `(shard_idx, batch_idx)` cursor, and Python/NumPy/PyTorch CPU & CUDA RNG states. Training seamlessly resumes from step `K + 1`.

---

## 10. Checkpoint Recovery Procedure

If a runtime crashes during a write:
- Checkpoints are saved atomically into `.tmp_checkpoint_<step>_<uuid>` before atomic directory promotion to `checkpoint-<step>`.
- Any incomplete temporary folders are automatically purged by `_cleanup_stale_temp_dirs()`.
- If a checkpoint directory is truncated or missing files, `CheckpointManager.get_latest_checkpoint()` detects it via `is_checkpoint_valid()` and rolls back to the previous valid checkpoint.

---

## 11. Expected Artifacts

At step 100,000, the pretraining run produces:
- `/content/drive/MyDrive/nexa/checkpoints/pretrain/checkpoint-100000/training_state.pt`
- `/content/drive/MyDrive/nexa/checkpoints/pretrain/checkpoint-100000/training_config.json`
- Pretraining loss logs in `/content/drive/MyDrive/nexa/logs/pretrain/`

---

## 12. Stop / Failure Conditions

1. **VRAM Ceiling Violation**: If peak allocated VRAM exceeds 70% (> 10.5 GB on T4), the process terminates immediately.
2. **Missing Dataset**: If shards are not located at `--dataset-dir`, pretraining aborts with `FileNotFoundError`.
3. **Identity Mismatch**: If checkpoint dataset version or tokenizer hash does not match current code configuration, pretraining aborts with `ValueError`.
