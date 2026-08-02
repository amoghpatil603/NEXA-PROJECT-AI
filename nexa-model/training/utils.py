import random
import numpy as np
import torch
import os
import psutil

def set_seed(seed: int = 42):
    """
    Sets deterministic seed across random, numpy, and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def clip_gradients(model: torch.nn.Module, max_norm: float = 1.0):
    """
    Clips gradient norms.
    """
    return torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm)

def get_device(preferred: str = "cpu"):
    """
    Returns device with CPU fallback.
    """
    if preferred == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def get_rss_mb():
    """
    Returns current RSS memory in megabytes.
    """
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    return int(parts[1]) / 1024.0
    except:
        pass
    return psutil.Process(os.getpid()).memory_info().rss / 1024.0 / 1024.0
