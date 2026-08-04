import math
from torch.optim.lr_scheduler import LambdaLR

def get_cosine_schedule_with_warmup(optimizer, warmup_steps: int, max_steps: int, min_lr_ratio: float = 0.1):
    """
    Creates a learning rate scheduler with linear warmup and cosine decay.
    """
    def lr_lambda(current_step: int):
        if current_step < warmup_steps:
            if warmup_steps == 0:
                return 1.0
            return float(current_step) / float(max(1, warmup_steps))
        
        progress = float(current_step - warmup_steps) / float(max(1, max_steps - warmup_steps))
        progress = max(0.0, min(1.0, progress))
        
        # Cosine decay from 1.0 down to min_lr_ratio
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay

    return LambdaLR(optimizer, lr_lambda)
