try:
    import torch
except ImportError:
    torch = None
import os
from .config import TrainingConfig
from .optimizer import create_optimizer, create_scheduler
from .checkpoints import CheckpointManager
from .metrics import MetricsLogger

import contextlib

class Trainer:
    def __init__(self, model, config: TrainingConfig, dataloader):
        self.model = model
        self.config = config
        self.dataloader = dataloader
        self.device = self._detect_device()
        if hasattr(self.model, 'to'): self.model.to(self.device)
        
        self.optimizer = create_optimizer(self.model, self.config.learning_rate, self.config.weight_decay)
        self.scheduler = create_scheduler(self.optimizer, self.config.warmup_steps, self.config.max_steps)
        self.checkpoint_manager = CheckpointManager(self.config.checkpoint_dir)
        self.logger = MetricsLogger(self.config.log_dir)
        
        self.scaler = torch.cuda.amp.GradScaler(enabled=self.config.mixed_precision and self.device.type == 'cuda') if torch and hasattr(torch, "cuda") and hasattr(torch.cuda, "amp") and hasattr(torch.cuda.amp, "GradScaler") else None
        
        self.micro_step = 0
        self.optimizer_step = 0
        self.epoch = 0

    def _detect_device(self):
        if torch is None:
            return "cpu"
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def resume_from_checkpoint(self):
        latest = self.checkpoint_manager.get_latest_checkpoint()
        if latest:
            print(f"Resuming from checkpoint {latest}")
            self.optimizer_step, self.micro_step, self.epoch = self.checkpoint_manager.load(
                latest, self.model, self.optimizer, self.scheduler, self.dataloader, self.scaler
            )
            

