import torch
import psutil
import os

def get_memory_usage():
    """Returns the current memory usage of the process in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def clear_cuda_cache():
    """Clears the CUDA cache if a GPU is available."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
