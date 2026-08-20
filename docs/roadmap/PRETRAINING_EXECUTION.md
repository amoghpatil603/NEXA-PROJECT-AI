# NEXA Authoritative Foundation Pretraining Guide (Colab Tesla T4)

This document provides the authoritative, exact execution commands and procedures for running full pretraining of the **NEXA Tiny Foundation Model** on an NVIDIA Tesla T4 GPU (Google Colab / Cloud GPU).

---

## 1. Pretraining Specifications

- **Starting Repository SHA**: `ab09fa30bc164d07d9f1b3c295758cf7c1107304` (or subsequent HEAD)
- **Model Architecture**: `NexaConfig.tiny()`
  - Layers: `12`
  - Hidden Dimension (`d_model`): `512`
  - Heads: `8`
  - FFN Dimension (`d_ff`): `1792`
  - Vocabulary Size: `8000`
  - Max Sequence Length: `2048`
  - Parameter Count: **49,721,856** parameters
- **Canonical Dataset Location**: `data/shards` (Memory-mapped uint16 binary shards `data/shards/train/*.bin`)
- **Tokenizer**: `backend/tokenizer_v1/tokenizer.json` (`vocab_size=8000`)
- **Precision**: Automatic Mixed Precision (`torch.autocast(device_type='cuda')` + `GradScaler`)

---

## 2. Hardware Memory Safety Validation (Tesla T4)

- **Total GPU VRAM**: ~14.56 GB
- **Weights & Optimizer State**: ~0.7 GB
- **Batch Size**: `8`
- **Sequence Length**: `2048`
- **Gradient Accumulation**: `4` (Effective batch size = 32 sequences = 65,536 tokens/step)
- **Estimated Peak VRAM**: **~3.8 GB** (Headroom: **~10.7 GB / 73%**)
- **Safety Rating**: **PASSED** ✅ (Zero OOM risk under mixed precision)

---

## 3. Exact Execution Commands

### A. Environment Initialization (Colab T4 Notebook)
```bash
!git clone https://github.com/amoghpatil603/NEXA-PROJECT-AI.git
%cd NEXA-PROJECT-AI
!git checkout main
!pip install -r requirements.txt pytest
```

### B. Dry-Run Sanity Check
```bash
python scripts/train_pretrain.py --dry-run
```

### C. Full 100,000-Step Pretraining Command
```bash
python scripts/train_pretrain.py \
    --batch-size 8 \
    --grad-accum 4 \
    --lr 3e-4 \
    --weight-decay 0.1 \
    --warmup-steps 1000 \
    --max-steps 100000 \
    --save-steps 1000 \
    --log-steps 10 \
    --dataset-dir data/shards \
    --checkpoint-dir checkpoints/pretrain \
    --log-dir logs/pretrain \
    --seed 42
```

---

## 4. Checkpoints & State Recovery

- **Checkpoint Location**: `checkpoints/pretrain/checkpoint-{step}/training_state.pt`
- **Saved Metadata**:
  - Model weights (`model_state_dict`)
  - Optimizer states (`optimizer_state_dict`)
  - LR Scheduler state (`scheduler_state_dict`)
  - AMP GradScaler state (`scaler_state`)
  - RNG states (Python, NumPy, PyTorch CPU, PyTorch CUDA)
  - DataLoader cursor (`current_shard_idx`, `current_batch_idx`)
  - Configuration & identity hashes

### Exact Resume Command
```bash
# Automatically discovers latest checkpoint from --checkpoint-dir and resumes seamlessly
python scripts/train_pretrain.py \
    --batch-size 8 \
    --grad-accum 4 \
    --lr 3e-4 \
    --max-steps 100000 \
    --save-steps 1000 \
    --dataset-dir data/shards \
    --checkpoint-dir checkpoints/pretrain \
    --log-dir logs/pretrain
```

---

## 5. Success Criteria & Validation Gates

1. **Monotonic Convergence**: Loss steadily decreases from initial ~8.8 to < 2.5 on pretraining corpus.
2. **Gradient Stability**: Zero NaN/Inf loss scaling events under GradScaler.
3. **Periodic Checkpointing**: State checkpoint saved every 1,000 steps.
4. **Artifact Generation**: Final converged weights exported to `checkpoints/pretrain/checkpoint-100000/`.
