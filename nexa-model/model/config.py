import json
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

@dataclass
class NexaConfig:
    vocab_size: int = 8000
    max_seq_len: int = 256
    d_model: int = 256
    n_layers: int = 4
    n_heads: int = 8
    d_ff: int = 1024
    dropout: float = 0.1
    norm_eps: float = 1e-5
    weight_tying: bool = True
    bias: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    def save(self, path: str | Path):
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str | Path) -> "NexaConfig":
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)
