import torch

def create_optimizer(model, learning_rate: float, weight_decay: float):
    if not hasattr(torch.optim, "AdamW"):
        return None # Graceful failure if torch is a dummy
        
    param_optimizer = list(model.named_parameters())
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
         'weight_decay': weight_decay},
        {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
    ]
    return torch.optim.AdamW(optimizer_grouped_parameters, lr=learning_rate)

def create_scheduler(optimizer, warmup_steps: int, max_steps: int):
    # Dummy linear scheduler for simplicity if torch is available
    if optimizer is None: return None
    def lr_lambda(current_step: int):
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        return max(0.0, float(max_steps - current_step) / float(max(1, max_steps - warmup_steps)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
