import torch
import torch.nn as nn
from contextlib import nullcontext
from typing import Dict, Any, Optional
from .utils import clip_gradients

class Trainer:
    """
    Encapsulates training steps with mixed precision, gradient accumulation, clipping, and optimizer updates.
    """
    def __init__(self, model: nn.Module, optimizer: torch.optim.Optimizer, scheduler: Optional[Any], config: Any):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.config = config
        self.global_step = 0
        
        self.device = next(self.model.parameters()).device
        self.precision = getattr(config, "precision", "auto").lower()
        
        # Setup mixed precision context & scaler
        self.autocast_ctx = self._setup_autocast()
        self.scaler = self._setup_scaler()

    def _setup_autocast(self):
        if self.precision == "fp32":
            return nullcontext()
            
        if self.device.type == "cuda":
            dtype = torch.float16 if self.precision == "fp16" else torch.bfloat16
            return torch.amp.autocast("cuda", dtype=dtype)
        elif self.device.type == "cpu" and self.precision == "bf16":
            return torch.amp.autocast("cpu", dtype=torch.bfloat16)
        else:
            return nullcontext()

    def _setup_scaler(self):
        if self.device.type == "cuda" and self.precision == "fp16":
            return torch.cuda.amp.GradScaler(enabled=True)
        return None

    def training_step(self, batch_inputs: torch.Tensor, batch_targets: torch.Tensor, accumulate: bool = True) -> Dict[str, Any]:
        self.model.train()
        
        inputs = batch_inputs.to(self.device)
        targets = batch_targets.to(self.device)
        
        with self.autocast_ctx:
            logits, loss = self.model(inputs, targets)
            loss_scaled = loss / self.config.gradient_accumulation_steps

        if self.scaler is not None:
            self.scaler.scale(loss_scaled).backward()
        else:
            loss_scaled.backward()

        grad_norm = None
        did_update = False

        if not accumulate:
            if self.scaler is not None:
                self.scaler.unscale_(self.optimizer)
                grad_norm = clip_gradients(self.model, self.config.grad_clip)
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                grad_norm = clip_gradients(self.model, self.config.grad_clip)
                self.optimizer.step()

            if self.scheduler is not None:
                self.scheduler.step()

            self.optimizer.zero_grad(set_to_none=True)
            self.global_step += 1
            did_update = True

        return {
            "loss": loss.detach().item(),
            "grad_norm": grad_norm.item() if grad_norm is not None else 0.0,
            "global_step": self.global_step,
            "did_update": did_update
        }
