import torch
import os
from pathlib import Path
from .trainer import Trainer
from .checkpoint import save_checkpoint, load_checkpoint
from .metrics import MetricsLogger
from .utils import get_rss_mb, set_seed

class TrainLoop:
    """
    Coordinates training loop with automatic checkpointing, metrics logging, and interruption recovery.
    """
    def __init__(self, model, dataloader, optimizer, scheduler, config):
        self.model = model
        self.dataloader = dataloader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.config = config
        self.trainer = Trainer(model, optimizer, scheduler, config)
        self.logger = MetricsLogger(config.output_dir)
        set_seed(config.seed)

    def run(self, max_steps=None):
        max_steps = max_steps or self.config.max_steps
        data_iter = iter(self.dataloader)
        
        accumulation_loss = 0.0
        steps_accumulated = 0
        
        for step in range(1, max_steps + 1):
            try:
                batch_inputs, batch_targets = next(data_iter)
            except StopIteration:
                data_iter = iter(self.dataloader)
                batch_inputs, batch_targets = next(data_iter)
                
            is_last_micro = (steps_accumulated + 1 == self.config.gradient_accumulation_steps)
            accumulate = not is_last_micro
            
            step_info = self.trainer.training_step(batch_inputs, batch_targets, accumulate=accumulate)
            accumulation_loss += step_info["loss"]
            steps_accumulated += 1
            
            if is_last_micro:
                avg_loss = accumulation_loss / self.config.gradient_accumulation_steps
                current_lr = self.optimizer.param_groups[0]["lr"]
                
                metrics = {
                    "global_step": self.trainer.global_step,
                    "loss": avg_loss,
                    "lr": current_lr,
                    "grad_norm": step_info["grad_norm"],
                    "rss_mb": get_rss_mb()
                }
                
                self.logger.log(metrics)
                
                if self.trainer.global_step % self.config.save_every_steps == 0:
                    self.save_state()
                    
                accumulation_loss = 0.0
                steps_accumulated = 0

    def save_state(self, filename="checkpoint_latest.pt"):
        state = {
            "global_step": self.trainer.global_step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None,
            "rng_state": torch.get_rng_state(),
            "config": self.config
        }
        return save_checkpoint(state, self.config.output_dir, filename)

    def load_state(self, filepath):
        checkpoint = load_checkpoint(filepath, self.model, self.optimizer, self.scheduler)
        self.trainer.global_step = checkpoint.get("global_step", 0)
        return checkpoint
