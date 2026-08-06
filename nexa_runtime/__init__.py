from nexa_runtime.core.manager import RuntimeManager
from nexa_runtime.loaders.model_loader import ModelLoader
from nexa_runtime.providers.local import LocalProvider
from nexa_runtime.services.memory import MemoryManager
from nexa_runtime.services.tools import ToolRegistry
from nexa_runtime.services.rag import RAGService

class NexaRuntime:
    """Unified Public API for the NEXA SDK."""
    def __init__(self, checkpoint_dir=None):
        self.manager = RuntimeManager()
        self.loader = ModelLoader(checkpoint_dir) if checkpoint_dir else ModelLoader()
        self.engine = LocalProvider(self.loader)
        self.memory = MemoryManager()
        self.tools = ToolRegistry()
        self.rag = RAGService()

    def start(self):
        return self.manager.startup()

    def generate(self, prompt, **kwargs):
        return self.engine.generate(prompt, **kwargs)

    def get_health(self):
        return self.manager.get_health()
