import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint
from .config import NexaConfig
from .attention import CausalSelfAttention
from .mlp import MLP
from .norm import RMSNorm

class Block(nn.Module):
    def __init__(self, config: NexaConfig):
        super().__init__()
        norm_type = getattr(config, "norm_type", "layernorm").lower()
        if norm_type == "rmsnorm":
            self.ln_1 = RMSNorm(config.d_model, eps=config.norm_eps)
            self.ln_2 = RMSNorm(config.d_model, eps=config.norm_eps)
        else:
            self.ln_1 = nn.LayerNorm(config.d_model, eps=config.norm_eps)
            self.ln_2 = nn.LayerNorm(config.d_model, eps=config.norm_eps)

        self.attn = CausalSelfAttention(config)
        self.mlp = MLP(config)
        self.gradient_checkpointing = getattr(config, "gradient_checkpointing", False)

    def _forward_block(self, x, layer_past=None):
        attn_out, present = self.attn(self.ln_1(x), layer_past=layer_past)
        x = x + attn_out
        x = x + self.mlp(self.ln_2(x))
        return x, present

    def forward(self, x, layer_past=None):
        if self.training and self.gradient_checkpointing:
            return checkpoint(self._forward_block, x, layer_past)
        return self._forward_block(x, layer_past=layer_past)
