from abc import ABC, abstractmethod

class InferenceEngine(ABC):
    """Abstract base class for all NEXA inference engines."""
    def __init__(self, model_loader):
        self.loader = model_loader

    @abstractmethod
    def generate(self, prompt, max_tokens=128, temperature=0.7):
        pass

    @abstractmethod
    def stream(self, prompt, max_tokens=128, temperature=0.7):
        pass
