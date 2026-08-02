import dataclasses
from typing import Optional

@dataclasses.dataclass
class TrainingConfig:
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    warmup_steps: int = 100
    max_steps: int = 1000
    min_lr_ratio: float = 0.1
    grad_clip: float = 1.0
    gradient_accumulation_steps: int = 8
    micro_batch_size: int = 1
    context_len: int = 256
    seed: int = 42
    output_dir: str = "checkpoints"
    save_every_steps: int = 100
    log_every_steps: int = 10
    device: str = "cpu"
