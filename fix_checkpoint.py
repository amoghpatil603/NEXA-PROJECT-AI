import sys
import torch
import os
sys.path.insert(0, 'nexa-model')
from model.config import NexaConfig
from model.transformer import NexaTransformer

config = NexaConfig(
    vocab_size=8000,
    max_seq_len=256,
    d_model=384,
    n_layers=6,
    n_heads=6,
    d_ff=1536,
    dropout=0.1,
    norm_eps=1e-5,
    weight_tying=True
)
model = NexaTransformer(config)
os.makedirs("checkpoints", exist_ok=True)
torch.save({"model_state_dict": model.state_dict()}, "checkpoints/model.pt")
print("Saved dummy checkpoint to checkpoints/model.pt")
