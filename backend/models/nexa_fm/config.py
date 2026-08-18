import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

def _get_default_vocab_size() -> int:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "tokenizer_v1/tokenizer_config.json",
        Path("backend/tokenizer_v1/tokenizer_config.json"),
        Path("tokenizer_v1/tokenizer_config.json")
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data["vocab_size"]
            except Exception:
                pass
    return 300

@dataclass
class NexaFMConfig:
    vocab_size: int = _get_default_vocab_size()
    hidden_size: int = 768
    num_layers: int = 12
    num_heads: int = 12
    max_context_length: int = 4096
    activation_function: str = "gelu"
    dropout_prob: float = 0.1
    initializer_range: float = 0.02
    layer_norm_eps: float = 1e-5
    use_rotary_embeddings: bool = True


    @classmethod
    def small(cls) -> "NexaFMConfig":
        return cls(hidden_size=512, num_layers=8, num_heads=8)

    @classmethod
    def base(cls) -> "NexaFMConfig":
        return cls(hidden_size=768, num_layers=12, num_heads=12)

    @classmethod
    def large(cls) -> "NexaFMConfig":
        return cls(hidden_size=1536, num_layers=24, num_heads=16)

    @classmethod
    def tiny(cls) -> "NexaFMConfig":
        return cls(hidden_size=128, num_layers=4, num_heads=4, max_context_length=128)
