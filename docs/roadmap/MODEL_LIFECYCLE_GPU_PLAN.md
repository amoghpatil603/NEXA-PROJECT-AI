# NEXA Model Lifecycle GPU Execution Plan

This document defines the authoritative, reproducible GPU execution roadmap for the NEXA model lifecycle. All compute-intensive, long-running training, alignment, and benchmark jobs are deferred to dedicated GPU environments (e.g. Google Colab Tesla T4 / Cloud GPU).

---

## 1. Stage Overview & Resource Allocation

| Stage | Objective | Execution Target | GPU Class | Est. Runtime |
|---|---|---|---|---|
| **A. Full Pretraining** | 49.7M Param Tiny Foundation Model Pretraining | `scripts/train_pretrain.py` | Tesla T4 / A100 | 12–24 Hours |
| **B. Supervised Fine-Tuning (SFT)** | Conversational & Instruction Alignment | `scripts/train_sft.py` | Tesla T4 | 2–4 Hours |
| **C. Preference Optimization (DPO)** | Pairwise Safety & Quality Alignment | `scripts/train_dpo.py` | Tesla T4 | 1–2 Hours |
| **D. Benchmark Evaluation** | Multi-domain Accuracy, Perplexity & Safety | `evaluate_model.py` / `backend/eval` | Tesla T4 | 30 Mins |
| **E. Model Export & Quantization** | PyTorch / INT8 / SafeTensors Packaging | `scripts/export_model.py` | Tesla T4 / CPU | 15 Mins |
| **F. Final Deployment Validation** | Full Inference Engine & API Contract Check | `backend/api/ai_service.py` | Tesla T4 / CPU | 15 Mins |

---

## 2. Stage-by-Stage Detailed Workflows

### A. Foundation Pretraining
- **Execution Command**:
  ```bash
  python scripts/train_pretrain.py \
      --batch-size 8 \
      --grad-accum 4 \
      --lr 3e-4 \
      --warmup-steps 1000 \
      --max-steps 100000 \
      --save-steps 1000 \
      --dataset-dir data/shards \
      --checkpoint-dir checkpoints/pretrain
  ```
- **Authoritative Configuration**: `NexaConfig.tiny()` (vocab_size=8000, max_seq_len=2048, d_model=512, n_layers=12, n_heads=8, d_ff=1792, weight_tying=True, pos_type="rope", norm_type="rmsnorm").
- **Dataset**: `data/shards/*.bin` (Tokenized uint16 memory-mapped binary shards).
- **Expected Artifact**: `checkpoints/pretrain/checkpoint-100000/training_state.pt` & `best.ckpt`.
- **Resume Strategy**: Automatic checkpoint discovery via `CheckpointManager.get_latest_checkpoint()` restoring model weights, AdamW momentum buffers, and shard/batch dataloader cursors.
- **Validation Gate**: Training loss curve monotonic descent; perplexity < 15.0 on validation holdout.
- **Estimated Resource Class**: HIGH (Tesla T4 GPU, 14.56 GB VRAM).
- **Success Criterion**: Stable convergence over 100k steps with zero NaN/Inf gradients.

---

### B. Supervised Fine-Tuning (SFT)
- **Execution Command**:
  ```bash
  python scripts/train_sft.py \
      --base-checkpoint checkpoints/pretrain/best.ckpt \
      --data-file data/instruction_dataset.jsonl \
      --batch-size 4 \
      --grad-accum 4 \
      --lr 2e-5 \
      --max-steps 1500 \
      --checkpoint-dir checkpoints/sft
  ```
- **Dataset**: `data/instruction_dataset.jsonl` (Chat formatted with assistant loss masking).
- **Expected Artifact**: `checkpoints/sft/best.ckpt`.
- **Resume Strategy**: Loads base pretrained weights, initial warm optimizer step.
- **Validation Gate**: Multi-turn dialogue evaluation loss < 0.5; assistant loss masking verified.
- **Estimated Resource Class**: MEDIUM (Tesla T4 GPU).
- **Success Criterion**: Accurate instruction following and valid EOS token generation.

---

### C. Direct Preference Optimization (DPO)
- **Execution Command**:
  ```bash
  python scripts/train_dpo.py \
      --sft-checkpoint checkpoints/sft/best.ckpt \
      --preference-data data/preference_dataset.jsonl \
      --batch-size 2 \
      --grad-accum 4 \
      --lr 5e-6 \
      --beta 0.1 \
      --max-steps 500 \
      --checkpoint-dir checkpoints/dpo
  ```
- **Dataset**: `data/preference_dataset.jsonl` (Pairwise prompt, chosen, rejected JSONL).
- **Expected Artifact**: `checkpoints/dpo/best.ckpt`.
- **Resume Strategy**: Policy model initialized from SFT checkpoint; frozen reference model initialized in `eval()` mode.
- **Validation Gate**: Reward margin $(r_{\text{chosen}} - r_{\text{rejected}}) > 0$ on > 90% of validation pairs.
- **Estimated Resource Class**: MEDIUM (Tesla T4 GPU).
- **Success Criterion**: Measurable reduction in dispreferred/harmful completions while maintaining conversational fluency.

---

### D. Benchmark Evaluation
- **Execution Command**:
  ```bash
  python -m backend.eval.runner \
      --checkpoint checkpoints/dpo/best.ckpt \
      --benchmarks mmlu_tiny,gsm8k_tiny,reasoning \
      --output-report reports/evaluation_final.json
  ```
- **Dataset**: Structured EvaluationCase benchmarks.
- **Expected Artifact**: `reports/evaluation_final.json`.
- **Validation Gate**: Exact match / token accuracy exceeds target baseline (> 85% accuracy on domain tasks).
- **Estimated Resource Class**: LOW–MEDIUM.
- **Success Criterion**: Full benchmark report with zero execution crashes.

---

### E. Model Export & Packaging
- **Execution Command**:
  ```bash
  python scripts/export_model.py \
      --checkpoint checkpoints/dpo/best.ckpt \
      --output-dir models/nexa_tiny_v1 \
      --filename model.pt
  ```
- **Expected Artifact**: `models/nexa_tiny_v1/model.pt`, `config.json`, `manifest.json`.
- **Validation Gate**: Format integrity tests load exported weights without key mismatch.
- **Estimated Resource Class**: LOW.
- **Success Criterion**: Production-ready deployment folder with verified checksums.

---

### F. Final Deployment Verification
- **Execution Command**:
  ```bash
  uvicorn backend.api.ai_service:app --host 0.0.0.0 --port 8000
  ```
- **Expected Artifact**: Active OpenAPI endpoints `/health`, `/v1/chat/completions`.
- **Validation Gate**: HTTP 200 on `/health` returning `model_loaded: true`.
- **Estimated Resource Class**: LOW.
- **Success Criterion**: Streaming tokens emitted over SSE with latency < 50ms per token.
