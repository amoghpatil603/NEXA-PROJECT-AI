# Training Engine Architecture

## Overview
The NEXA Training Engine is a modular, scalable PyTorch-based training loop designed to facilitate the training of the NEXA Foundation Model. It handles hardware abstraction, distributed readiness, checkpoining, and logging.

## Modules

### 1. `Trainer`
The core class that orchestrates the training loop. It handles:
- Forward/backward passes.
- Gradient accumulation.
- Mixed precision scaling (AMP).
- Gradient clipping.
- Scheduling and checkpointing.

### 2. `TrainingConfig`
A strongly typed dataclass defining training hyperparameters, directories, and limits. It includes built-in serialization mechanisms (JSON).

### 3. `ShardDataLoader`
A custom dataloader that streams directly from the JSONL shards created by the Dataset Pipeline. It automatically applies chunking to match `max_length`.

### 4. `CheckpointManager`
A robust saving and loading mechanism for PyTorch models. It captures:
- Model Weights.
- Optimizer/Scheduler state.
- Global Step & Epoch.

### 5. `MetricsLogger`
Handles structured JSONL logging for telemetry, capturing loss, learning rate, and global steps.
