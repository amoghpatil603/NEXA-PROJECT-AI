import torch
from nexa_runtime.engine.base import InferenceEngine

class LocalProvider(InferenceEngine):
    """Handles local inference using PyTorch."""
    def __init__(self, model_loader, device=None):
        super().__init__(model_loader)
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None

    def generate(self, prompt, max_tokens=128, temperature=0.7):
        if not self.loader.loaded_model:
            return "[ERROR] Model not loaded in ModelLoader."
        
        self.model = self.loader.loaded_model.to(self.device)
        self.model.eval()
        
        # Simulated generation logic for structure verification
        tokens = [ord(c) % 256 for c in prompt]
        input_tensor = torch.tensor([tokens]).to(self.device)
        
        with torch.no_grad():
            # Verification forward pass
            try:
                _ = self.model(input_tensor)
                return f"[LOCAL_PROV] Success: Mock response for '{prompt[:20]}...'"
            except Exception as e:
                return f"[LOCAL_PROV] Generation Error: {str(e)}"

    def stream(self, prompt, max_tokens=128, temperature=0.7):
        yield "[LOCAL_STREAM] Starting..."
        yield "Done."
