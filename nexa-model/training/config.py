import json
import dataclasses
from typing import Optional
from pathlib import Path

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
    precision: str = "auto"
    gradient_checkpointing: bool = False
    seed: int = 42
    output_dir: str = "checkpoints"
    eval_every_steps: int = 50
    save_every_steps: int = 100
    log_every_steps: int = 10
    early_stopping_patience: Optional[int] = None
    keep_last_n_checkpoints: int = 3
    device: str = "cpu"
    tensorboard_dir: Optional[str] = "runs"
    tokenizer_version: str = "1.0.0"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def save(self, path: str | Path):
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str | Path) -> "TrainingConfig":
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)
