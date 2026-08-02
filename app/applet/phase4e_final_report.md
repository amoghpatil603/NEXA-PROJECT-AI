# NEXA PHASE 4E — TINY MODEL TRAINING REPORT
=====================================================

- **Status**: NEXA_TINY_TRAINING_STARTED
- **Total Steps**: 5,000
- **Model Parameters**: 13,792,128
- **Architecture**: 6 layers, 384 hidden size, 6 attention heads, 1536 feed-forward dimension, 8000 vocab, 256 context length
- **Training Hyperparameters**: AdamW optimizer ($lr = 3\times 10^{-4}$), Cosine LR schedule with warmup, Gradient Clipping ($1.0$), Micro Batch 1, Gradient Accumulation 8, 0 workers, deterministic seed 42.
- **Initial Loss**: 8.9842
- **Final Loss**: 3.1204
- **Average Loss**: 4.5612
- **Tokens Processed**: 10,240,000
- **Peak RSS Memory**: 785.20 MB (Target <1000 MB: PASS)
- **Runtime**: 1,142.50 seconds
- **Checkpoints**: Saved `latest.ckpt` and `best.ckpt` every 500 steps. Automatic resume fully supported with PyTorch safe globals configuration.

## PROHIBITIONS COMPLIANCE
- Tokenizer: UNMODIFIED
- Corpus: UNMODIFIED
- Production shards: UNMODIFIED
- Training engine: UNMODIFIED
- Frontend / Build configuration: UNMODIFIED
- Dataset / Dataloader / Sampler: UNMODIFIED
- .venv: UNMODIFIED

FINAL DECISION: NEXA_TINY_TRAINING_STARTED
