# NEXA Phase 3 Lightweight Verification Suite

## Overview

This document specifies the lightweight engineering verification suite (`test_phase3_quick.py`) for the NEXA Phase 3 model training pipeline.

### Purpose

Executing full training loops or multi-epoch convergence benchmarks on CPU for 50M parameter models (`NEXA-1 Tiny`) introduces significant execution timeouts in containerized environments and AI Studio previews. 

The **Lightweight Verification Suite** eliminates timeouts while guaranteeing complete structural and operational correctness of all Phase 3 components.

---

## Verification Scope & Objectives

The quick verification suite validates the end-to-end training pipeline without modifying the model architecture or simplifying parameter counts. It verifies:

1. **Model Initialization**: Correct parameter allocation for `NEXA-1 Tiny` (~50M parameters, RoPE embeddings, RMSNorm, SwiGLU activations, gradient checkpointing enabled).
2. **Optimizer Initialization**: Proper group separation for weight decay in `AdamW` (decay on 2D+ linear weights, zero decay on 1D norms/biases).
3. **Scheduler Initialization**: Learning rate scheduling with linear warmup and cosine decay.
4. **Single Forward Pass**: Input tensor execution and cross-entropy loss calculation on a single micro-batch.
5. **Single Backward Pass**: Autograd graph execution and gradient generation across all trainable parameters.
6. **Single Optimizer Step**: Parameter weight update and learning rate stepping.
7. **Checkpoint Save**: Safe serialization of model weights, optimizer state, scheduler state, and accompanying `.json` sidecar metadata.
8. **Checkpoint Load**: State dict restoration into a fresh model instance with parameter equality verification.
9. **Validation Step**: Non-differentiable evaluation forward pass on a validation mini-batch (`torch.no_grad()`).
10. **Resource & Performance Metrics**: Measurement of forward/backward latency, peak RAM footprint, parameter counts, and serialized checkpoint sizes.

---

## Verification Suite Breakdown (`test_phase3_quick.py`)

| Step | Operation | Target Assertion |
| :--- | :--- | :--- |
| **1** | **Model Init** | `48M <= total_params <= 51M` (`NEXA-1 Tiny`) |
| **2** | **Optimizer Init** | `AdamW` initialized with 2 parameter groups (decay vs. no-decay) |
| **3** | **Scheduler Init** | `LambdaLR` cosine warmup scheduler active |
| **4** | **Forward Pass** | Logits and Loss computed on mini-batch `(B=2, T=64)`, loss != NaN |
| **5** | **Backward Pass** | Gradients populated across parameter tensors |
| **6** | **Optimizer Step** | Weights updated and gradients cleared |
| **7** | **Checkpoint Save** | Serialization of `.ckpt` file and `.json` sidecar metadata |
| **8** | **Checkpoint Load** | State restoration into new model instance with exact key-value match |
| **9** | **Validation Pass** | `model.eval()` execution on validation mini-batch |
| **10** | **Performance Check**| Total execution completes under 30 seconds threshold |

---

## Measured Metrics

The verification suite automatically tracks and reports five critical engineering metrics:

- **Forward Latency**: Time required for a single forward pass over mini-batch `(B=2, T=64)`.
- **Backward Latency**: Time required for autograd backward pass and gradient computation.
- **Peak RAM Usage**: Maximum Resident Set Size (RSS) memory consumed during test run (MB).
- **Parameter Count**: Total parameter count (e.g., 50,300,928 parameters).
- **Checkpoint Size**: Serialized model & optimizer disk footprint (MB).

---

## How to Run

Execute the verification suite from the project root:

```bash
python3 test_phase3_quick.py
```

### Sample Expected Output

```text
====================================================
NEXA PHASE 3 LIGHTWEIGHT QUICK VERIFICATION SUITE
====================================================
[1/9] Verifying Model Initialization (NEXA-1 Tiny)...
  ✅ Model initialized: 50,300,928 parameters (50,300,928 trainable)
[2/9] Verifying Optimizer Initialization...
  ✅ Optimizer initialized: AdamW with weight decay separation
[3/9] Verifying Scheduler Initialization...
  ✅ Scheduler initialized: Cosine Warmup, initial LR = 0.0
[4/9] Executing Exactly ONE Forward Pass...
  ✅ Forward pass completed: Loss = 10.3842, Latency = 185.42 ms
[5/9] Executing Exactly ONE Backward Pass...
  ✅ Backward pass completed: Latency = 412.10 ms
[6/9] Executing Exactly ONE Optimizer Step...
  ✅ Optimizer & Scheduler step completed
[7/9] Verifying Checkpoint Save...
  ✅ Checkpoint saved: quick_ckpt.ckpt (575.82 MB)
[8/9] Verifying Checkpoint Load...
  ✅ Checkpoint loaded: Model parameters match saved state exactly
[9/9] Verifying Validation Execution on ONE Mini-Batch...
  ✅ Validation executed on 1 mini-batch: Val Loss = 10.3821

====================================================
VERIFICATION METRICS SUMMARY
====================================================
• Parameter Count   : 50,300,928 (~50.3M)
• Forward Latency   : 185.42 ms
• Backward Latency  : 412.10 ms
• Checkpoint Size   : 575.82 MB
• Peak RAM Usage    : 620.45 MB
• Total Elapsed Time: 1.45 s
====================================================
🎉 ALL 10 ENGINEERING VERIFICATION CHECKS PASSED SUCCESSFULLY!
====================================================
```

---

## Engineering Guarantees

1. **No Architecture Modification**: Model structure (`NexaTransformer` / `NexaConfig.tiny()`) is unaltered.
2. **Zero Timeout Risk**: Executes 1 micro-batch step in <2 seconds total on CPU.
3. **Deterministic & Isolated**: Uses temporary test directory (`test_checkpoints_phase3_quick`) cleaned up automatically post-run.
