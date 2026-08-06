import torch
import sys
import os
from pathlib import Path
from model.config import NexaConfig
from model.transformer import NexaTransformer

class NexaModelLoader:
    @staticmethod
    def load(checkpoint_path, config=None, device='cpu'):
        print(f"Loading checkpoint from: {checkpoint_path}")
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path, map_location=device)
        
        if config is None:
             # Default to the Tiny config used in training
             config = NexaConfig(vocab_size=8000, max_seq_len=256, d_model=384, n_layers=6, n_heads=6, d_ff=1536)

        model = NexaTransformer(config).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        print(f"\u2705 Model loaded successfully. Parameters: {sum(p.numel() for p in model.parameters()):,}")
        return model, config
