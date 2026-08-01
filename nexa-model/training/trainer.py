import torch
import torch.nn as nn
from .utils import clip_gradients

class Trainer:
    """
    Encapsulates training steps with gradient accumulation, clipping, and optimizer updates.
    """
    def __init__(self, model, optimizer, scheduler, config):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.config = config
        self.global_step = 0

    def training_step(self, batch_inputs, batch_targets, accumulate: bool = True):
        self.model.train()
        device = next(self.model.parameters()).device
        
        inputs = batch_inputs.to(device)
        targets = batch_targets.to(device)
        
        logits, loss = self.model(inputs, targets)
        
        # Scale loss for gradient accumulation
        loss_scaled = loss / self.config.gradient_accumulation_steps
        loss_scaled.backward()
        
        grad_norm = None
        did_update = False
        
        if not accumulate:
            grad_norm = clip_gradients(self.model, self.config.grad_clip)
            self.optimizer.step()
            if self.scheduler is not None:
                self.scheduler.step()
            self.optimizer.zero_grad()
            self.global_step += 1
            did_update = True
            
        return {
            "loss": loss.detach().item(),
            "grad_norm": grad_norm.item() if grad_norm is not None else 0.0,
            "global_step": self.global_step,
            "did_update": did_update
        }
