from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Any

@dataclass
class GenerationConfig:
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.0
    do_sample: bool = True
    seed: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.max_new_tokens, int) or self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be an integer > 0")
        if not isinstance(self.temperature, (int, float)) or self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("temperature must be a float between 0.0 and 2.0")
        if not isinstance(self.top_k, int) or self.top_k < 0:
            raise ValueError("top_k must be an integer >= 0")
        if not isinstance(self.top_p, (int, float)) or not (0.0 <= self.top_p <= 1.0):
            raise ValueError("top_p must be a float between 0.0 and 1.0")
        if not isinstance(self.repetition_penalty, (int, float)) or self.repetition_penalty < 1.0:
            raise ValueError("repetition_penalty must be a float >= 1.0")
        if not isinstance(self.do_sample, bool):
            raise ValueError("do_sample must be a boolean")
        if self.seed is not None and (not isinstance(self.seed, int) or self.seed < 0):
            raise ValueError("seed must be a non-negative integer")

@dataclass
class GenerationRequest:
    prompt: str
    config: Optional[GenerationConfig] = None

    def __post_init__(self):
        if not isinstance(self.prompt, str) or len(self.prompt.strip()) == 0:
            raise ValueError("prompt must be a non-empty string")
        if self.config is None:
            self.config = GenerationConfig()

@dataclass
class GenerationResult:
    text: str
    tokens_generated: int
    finish_reason: str

class CheckpointLoader(ABC):
    @abstractmethod
    def load_checkpoint(self, path: str) -> Any:
        """Load and validate model state from the given path."""
        pass

class InferenceEngine(ABC):
    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Run generation for the given request."""
        pass
