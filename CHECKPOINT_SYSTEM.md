# Checkpoint System

## Storage Format
Checkpoints are saved incrementally in the format: `checkpoint-{step}`.

Within each checkpoint folder:
- `training_state.pt`: Contains the weights of the Model, Optimizer, and Scheduler, alongside the global step and epoch counts.
- `training_config.json`: A JSON snapshot of the `TrainingConfig` used at the time of creation.

## Auto-Resume
The `Trainer.resume_from_checkpoint()` function scans the checkpoint directory and strictly selects the highest `step` value. It then injects the state back into the live variables.

## Google Drive Persistence
By storing checkpoints in `MyDrive/NEXA_FM/checkpoints`, the artifacts survive ephemeral Colab container resets.
