import json
from dataclasses import dataclass, field, asdict
import os

@dataclass
class TrainingConfig:
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    warmup_steps: int = 1000
    max_steps: int = 100000
    save_steps: int = 1000
    log_steps: int = 10
    max_grad_norm: float = 1.0
    mixed_precision: bool = True
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
    dataset_dir: str = "datasets/shards"
    seed: int = 42

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
