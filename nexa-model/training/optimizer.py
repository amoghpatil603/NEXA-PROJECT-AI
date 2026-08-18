import torch
import torch.nn as nn
from typing import Dict, Any

def configure_optimizers(
    model: nn.Module,
    weight_decay: float = 0.1,
    learning_rate: float = 3e-4,
    beta1: float = 0.9,
    beta2: float = 0.95,
    eps: float = 1e-8,
    device_type: str = "cpu"
) -> torch.optim.AdamW:
    """
    Configures AdamW optimizer with weight decay weight group separation.
    Parameters in 1D (biases, layernorm/rmsnorm weights, embedding) do NOT decay.
    2D+ parameters (linear weights) DO decay.
    """
    decay_params = []
    no_decay_params = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        # Biases and 1D parameters (Norm weights, etc.) do not decay
        if param.ndim < 2 or "bias" in name or "ln" in name or "norm" in name:
            no_decay_params.append(param)
        else:
            decay_params.append(param)

    optim_groups = [
        {"params": decay_params, "weight_decay": weight_decay},
        {"params": no_decay_params, "weight_decay": 0.0},
    ]

    # Use fused AdamW if supported and on CUDA
    fused_available = 'fused' in torch.optim.AdamW.__init__.__code__.co_varnames
    use_fused = fused_available and device_type == 'cuda'
    extra_args = dict(fused=True) if use_fused else dict()

    optimizer = torch.optim.AdamW(
        optim_groups,
        lr=learning_rate,
        betas=(beta1, beta2),
        eps=eps,
        **extra_args
    )
    return optimizer

def create_optimizer(*args, **kwargs):
    """Alias for configure_optimizers"""
    return configure_optimizers(*args, **kwargs)
