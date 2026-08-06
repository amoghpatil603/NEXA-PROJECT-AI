# Training Configuration Guide

The Training Engine is strictly driven by the `TrainingConfig` class in `backend.models.nexa_fm.training_engine.config`.

## Key Parameters
- `batch_size`: Hardware-dependent batch size.
- `gradient_accumulation_steps`: Simulates a larger batch size by updating weights every $N$ steps.
- `learning_rate`: Peak learning rate.
- `warmup_steps`: Steps until max LR is reached in Cosine schedule.
- `max_steps`: Total training duration.
- `mixed_precision`: Enables `torch.cuda.amp` to optimize VRAM and increase throughput.

## Swapping Configurations
Since it serializes to JSON, you can maintain `prod.json`, `debug.json`, and `experimental.json` and load them via `TrainingConfig.load("path/to/config.json")`.
