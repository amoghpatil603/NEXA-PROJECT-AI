from dataclasses import dataclass
from typing import Optional

@dataclass
class NexaFMConfig:
    vocab_size: int = 50257
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
