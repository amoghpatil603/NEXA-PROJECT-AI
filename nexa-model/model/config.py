import json
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

@dataclass
class NexaConfig:
    vocab_size: int = 8000
    max_seq_len: int = 2048
    d_model: int = 512
    n_layers: int = 12
    n_heads: int = 8
    d_ff: int = 1792
    dropout: float = 0.0
    norm_eps: float = 1e-5
    weight_tying: bool = True
    bias: bool = False
    activation: str = "swiglu"
    pos_type: str = "rope"
    norm_type: str = "rmsnorm"
    gradient_checkpointing: bool = False

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

    @classmethod
    def tiny(cls) -> "NexaConfig":
        """
        NEXA-1 Tiny Architecture Spec (49.72 Million Parameters)
        12 Layers, d_model=512, n_heads=8, d_ff=1792, vocab_size=8000
        """
        return cls(
            vocab_size=8000,
            max_seq_len=2048,
            d_model=512,
            n_layers=12,
            n_heads=8,
            d_ff=1792,
            dropout=0.0,
            norm_eps=1e-5,
            weight_tying=True,
            bias=False,
            activation="swiglu",
            pos_type="rope",
            norm_type="rmsnorm",
            gradient_checkpointing=False,
        )
