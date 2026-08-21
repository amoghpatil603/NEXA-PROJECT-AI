# NEXA — Master GPU Checklist & Work Breakdown

This document separates all work completed in software (in Antigravity on CPU) from the remaining tasks that strictly require GPU compute (Colab Tesla T4 / A100).

---

## 1. ALREADY COMPLETED IN SOFTWARE (CPU / Antigravity)

1. **Repository Audit & Baseline Verification**:
   - Baseline SHA verified against remote `origin/main`.
   - Complete gap analysis across all 20 architectural categories documented in `CURRENT_GAP_MATRIX.md`.

2. **Authoritative Tokenizer Canonicalization**:
   - Resolved single authoritative 8,000-vocabulary BPE tokenizer (`backend/models/tokenizer/production/tokenizer.json`).
   - Built `backend/models/tokenizer/canonical_resolver.py` providing unified resolution, SHA256 verification, and encode/decode consistency.
   - Added unit test suite `tests/phase2/test_authoritative_tokenizer.py`.

3. **Dataset External Storage Support & Error Handling**:
   - Hardened `ShardDataLoader` to support arbitrary external directories (Google Drive, local storage, persistent volumes).
   - Supported flat and nested (`train/`, `validation/`, `test/`) uint16 binary shard layouts with zero-copy memmap streaming.
   - Replaced all raw indexing crashes with descriptive `FileNotFoundError` / `ValueError` exceptions.
   - Added unit test suite `tests/phase2/test_dataset_discovery_and_errors.py`.

4. **Pretraining CLI & Safe Fallbacks**:
   - Hardened `scripts/train_pretrain.py` argument mappings.
   - Implemented CPU execution safeguard preventing accidental long CPU runs.
   - Added dry-run smoke testing validation.

5. **Checkpoint & Restart-Safe Resume Semantics**:
   - Hardened `CheckpointManager` and `ShardDataLoader.advance_cursor()` across shard boundaries.
   - Full restoration of Python, NumPy, PyTorch CPU, and PyTorch CUDA RNG states.
   - Added unit test suite `tests/phase2/test_pretrain_resume_boundaries.py` verifying exact next-batch tensor equality across restarts.

6. **Colab T4 Certification Script Overhaul**:
   - Updated `scripts/colab_t4_certification.py` with `--dataset-dir` support, explicit CUDA requirement, peak memory tracking (< 70% VRAM ceiling), and subprocess next-batch tensor equality validation.

7. **SFT Software Pipeline**:
   - Implemented `scripts/train_sft.py` CLI with assistant-only loss masking, chat formatting, and dry-run validation.

8. **DPO / RLHF Software Pipeline**:
   - Implemented `scripts/train_dpo.py` CLI with preference dataset loading, Bradley-Terry loss calculation, frozen reference model handling, and dry-run validation.

9. **Evaluation Harness**:
   - Implemented `scripts/run_eval.py` CLI supporting MMLU, GSM8K, HumanEval, and custom benchmark suites with structured JSON summary reporting.

10. **Model Export**:
    - Implemented `scripts/export_model.py` CLI with state dict export, configuration serialization, and manifest creation.

11. **Deployment Health & Readiness**:
    - Implemented `/health` and `/ready` endpoints with graceful degradation when models are not yet trained.
    - Added socket timeout guards to Redis client preventing hanging connections.

12. **CI/CD & Documentation**:
    - Verified CI compilation and lightweight testing workflows in `.github/workflows/ci.yml`.
    - Consolidated execution guides: `T4_EXECUTION_RUNBOOK.md`, `PRETRAINING_CHECKPOINT_RESUME.md`, `PRETRAINING_EXECUTION.md`.

---

## 2. MUST RUN ON GPU (Colab Tesla T4)

| ID | Task Name | Exact Command | Input Artifacts | Output Artifacts | Success Criteria | Checkpoint & Resume Strategy | Resource Req |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | **T4 Hardware & Resume Certification** | `python scripts/colab_t4_certification.py --dataset-dir /content/drive/MyDrive/nexa/shards --batch-size 1` | Shard dataset on Drive | Certification summary log | 49.72M params, 1-step/2-step peak VRAM < 70%, exact resumed tensor match | Temporary sub-process checkpoint test | Tesla T4 (~5 min) |
| **B** | **100k-Step Foundation Pretraining** | `python scripts/train_pretrain.py --dataset-dir /content/drive/MyDrive/nexa/shards --checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/pretrain --batch-size 8 --grad-accum 4 --max-steps 100000 --save-steps 1000` | Full binary shard dataset (`*.bin`) | `checkpoints/pretrain/checkpoint-100000/training_state.pt` | Loss curve monotonically decreasing, 100k steps completed | Saved every 1,000 steps; re-running command auto-resumes | Tesla T4 (~12-18 hrs total across sessions) |
| **C** | **Instruction Supervised Fine-Tuning (SFT)** | `python scripts/train_sft.py --base-checkpoint /content/drive/MyDrive/nexa/checkpoints/pretrain/checkpoint-100000/training_state.pt --data-file data/instruction_dataset.jsonl --batch-size 4 --grad-accum 4 --max-steps 1500 --checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/sft` | Pretrained base weights + `instruction_dataset.jsonl` | `checkpoints/sft/best.ckpt` | SFT conversational loss converges, assistant loss masking verified | Saved every 250 steps | Tesla T4 (~45 min) |
| **D** | **Direct Preference Optimization (DPO)** | `python scripts/train_dpo.py --sft-checkpoint /content/drive/MyDrive/nexa/checkpoints/sft/best.ckpt --preference-data data/preference_dataset.jsonl --batch-size 2 --grad-accum 4 --beta 0.1 --max-steps 500 --checkpoint-dir /content/drive/MyDrive/nexa/checkpoints/dpo` | SFT weights + `preference_dataset.jsonl` | `checkpoints/dpo/best.ckpt` | Chosen reward > Rejected reward margin increases | Saved every 100 steps | Tesla T4 (~30 min) |
| **E** | **Benchmark Suite Evaluation** | `python scripts/run_eval.py --checkpoint /content/drive/MyDrive/nexa/checkpoints/dpo/best.ckpt --benchmark all --output-dir logs/eval` | Aligned DPO/SFT model weights | `logs/eval/eval_all_report.json` | Benchmark scores computed for MMLU, GSM8K, HumanEval | Stateless evaluation run | Tesla T4 (~15 min) |
| **F** | **Deployment Artifact Export** | `python scripts/export_model.py --checkpoint /content/drive/MyDrive/nexa/checkpoints/dpo/best.ckpt --output-dir exported_model` | Final model checkpoint | `exported_model/model.pt`, `config.json`, `manifest.json` | Valid standalone deployment bundle | Non-checkpointed export script | Tesla T4 / CPU (~2 min) |
| **G** | **Heavy Multimodal Inference** | `python -m backend.vision.image_pipeline ...` | Vision/voice encoder weights | Processed multimodal outputs | High-resolution image/audio embeddings generated | Stateless inference | Tesla T4 (~10 min) |
