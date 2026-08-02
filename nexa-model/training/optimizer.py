import torch
import torch.nn as nn

def create_optimizer(model: nn.Module, learning_rate: float = 3e-4, weight_decay: float = 0.1, beta1: float = 0.9, beta2: float = 0.95, eps: float = 1e-8):
    """
    Creates AdamW optimizer with weight decay separation (no weight decay for biases and layer norms).
    Ensures every trainable parameter appears exactly once and verifies uniqueness of parameter IDs.
    """
    decay = []
    no_decay = []
    seen = set()

    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if id(p) in seen:
            continue
        seen.add(id(p))

        # Separate out biases, layer norms, embeddings, or 1D tensors vs 2D+ weights
        if name.endswith("bias") or "ln" in name or "norm" in name or "embed" in name or p.ndim < 2:
            no_decay.append(p)
        else:
            decay.append(p)

    param_groups = [
        {"params": decay, "weight_decay": weight_decay},
        {"params": no_decay, "weight_decay": 0.0},
    ]

    # Verify every parameter ID is unique across and within parameter groups
    param_ids = set()
    for group in param_groups:
        for p in group["params"]:
            pid = id(p)
            if pid in param_ids:
                raise ValueError(f"Parameter appears in more than one parameter group: {p}")
            param_ids.add(pid)

    optimizer = torch.optim.AdamW(param_groups, lr=learning_rate, betas=(beta1, beta2), eps=eps)
    return optimizer
