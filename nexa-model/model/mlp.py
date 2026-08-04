import torch
import torch.nn as nn
import torch.nn.functional as F
from .config import NexaConfig

class MLP(nn.Module):
    def __init__(self, config: NexaConfig):
        super().__init__()
        activation = getattr(config, "activation", "gelu").lower()
        self.is_swiglu = (activation == "swiglu")

        if self.is_swiglu:
            self.w1 = nn.Linear(config.d_model, config.d_ff, bias=config.bias)
            self.w2 = nn.Linear(config.d_model, config.d_ff, bias=config.bias)
            self.w3 = nn.Linear(config.d_ff, config.d_model, bias=config.bias)
        else:
            self.c_fc = nn.Linear(config.d_model, config.d_ff, bias=config.bias)
            self.gelu = nn.GELU(approximate="tanh")
            self.c_proj = nn.Linear(config.d_ff, config.d_model, bias=config.bias)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x):
        if self.is_swiglu:
            x = F.silu(self.w1(x)) * self.w2(x)
            x = self.w3(x)
        else:
            x = self.c_fc(x)
            x = self.gelu(x)
            x = self.c_proj(x)
        x = self.dropout(x)
        return x
