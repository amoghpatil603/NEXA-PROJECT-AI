import math
import torch
import torch.nn as nn
from typing import Optional, Any, Dict
from pathlib import Path

from .trainer import Trainer
from .checkpoint import save_checkpoint, load_checkpoint
from .metrics import MetricsLogger
from .utils import get_rss_mb, set_seed

class TrainLoop:
    """
    Coordinates full model training loop with gradient accumulation, evaluation,
    automatic checkpoint saving/resuming, metrics logging, and early stopping.
    """
    def __init__(
        self,
        model: nn.Module,
        train_dataloader: Optional[Any] = None,
        val_dataloader: Optional[Any] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        config: Optional[Any] = None,
        dataloader: Optional[Any] = None
    ):
        self.model = model
        self.train_dataloader = train_dataloader if train_dataloader is not None else dataloader
        self.val_dataloader = val_dataloader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.config = config
        
        self.trainer = Trainer(model, optimizer, scheduler, config)
        self.logger = MetricsLogger(
            output_dir=config.output_dir,
            tensorboard_dir=getattr(config, "tensorboard_dir", "runs")
        )
        
        self.best_val_loss = float("inf")
        self.no_improvement_count = 0
        set_seed(config.seed)

    def evaluate(self) -> Dict[str, float]:
        """
        Runs validation loop and calculates average loss and perplexity.
        """
        if self.val_dataloader is None:
            return {}

        self.model.eval()
        total_val_loss = 0.0
        val_steps = 0
        device = next(self.model.parameters()).device

        with torch.no_grad():
            for batch_inputs, batch_targets in self.val_dataloader:
                inputs = batch_inputs.to(device)
                targets = batch_targets.to(device)
                _, loss = self.model(inputs, targets)
                total_val_loss += loss.item()
                val_steps += 1

        avg_val_loss = total_val_loss / max(1, val_steps)
        perplexity = math.exp(min(avg_val_loss, 20.0))
        return {"val_loss": avg_val_loss, "perplexity": perplexity}

    def run(self, max_steps: Optional[int] = None):
        """
        Executes main training loop for given max_steps or config.max_steps.
        """
        target_max_steps = max_steps or self.config.max_steps
        data_iter = iter(self.train_dataloader)
        
        micro_loss_acc = 0.0
        micro_steps = 0
        
        while self.trainer.global_step < target_max_steps:
            try:
                batch_inputs, batch_targets = next(data_iter)
            except StopIteration:
                data_iter = iter(self.train_dataloader)
                batch_inputs, batch_targets = next(data_iter)

            micro_steps += 1
            is_last_micro = (micro_steps % self.config.gradient_accumulation_steps == 0)
            accumulate = not is_last_micro

            step_info = self.trainer.training_step(batch_inputs, batch_targets, accumulate=accumulate)
            micro_loss_acc += step_info["loss"]

            if step_info["did_update"]:
                avg_step_loss = micro_loss_acc / self.config.gradient_accumulation_steps
                current_lr = self.optimizer.param_groups[0]["lr"] if self.optimizer else 0.0
                step_num = self.trainer.global_step

                # 1. Logging
                if step_num % self.config.log_every_steps == 0:
                    metrics = {
                        "global_step": step_num,
                        "loss": avg_step_loss,
                        "lr": current_lr,
                        "grad_norm": step_info["grad_norm"],
                        "rss_mb": get_rss_mb()
                    }
                    self.logger.log(metrics)

                # 2. Evaluation & Best Model Checkpoint
                if self.val_dataloader is not None and (step_num % self.config.eval_every_steps == 0):
                    val_metrics = self.evaluate()
                    val_loss = val_metrics.get("val_loss", float("inf"))
                    
                    val_log = {
                        "global_step": step_num,
                        "val_loss": val_loss,
                        "perplexity": val_metrics.get("perplexity", 0.0)
                    }
                    self.logger.log(val_log)

                    if val_loss < self.best_val_loss:
                        self.best_val_loss = val_loss
                        self.no_improvement_count = 0
                        self.save_state(filename="best.ckpt", val_loss=val_loss)
                    else:
                        self.no_improvement_count += 1
                        if (getattr(self.config, "early_stopping_patience", None) is not None and
                            self.no_improvement_count >= self.config.early_stopping_patience):
                            print(f"Early stopping triggered at step {step_num}")
                            break

                # 3. Periodic Checkpoint Saving
                if step_num % self.config.save_every_steps == 0:
                    step_filename = f"ckpt_step_{step_num:06d}.ckpt"
                    self.save_state(filename="latest.ckpt", step_filename=step_filename)

                micro_loss_acc = 0.0
                micro_steps = 0

        # Ensure final state and best checkpoint exist upon loop finish
        self.save_state(filename="latest.ckpt")
        if self.val_dataloader is not None and not (Path(self.config.output_dir) / "best.ckpt").exists():
            val_metrics = self.evaluate()
            self.save_state(filename="best.ckpt", val_loss=val_metrics.get("val_loss", 0.0))

        self.logger.close()

    def save_state(self, filename: str = "latest.ckpt", step_filename: Optional[str] = None, val_loss: Optional[float] = None) -> str:
        """
        Saves current training state to checkpoint and sidecar metadata.
        """
        state = {
            "global_step": self.trainer.global_step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict() if self.optimizer else None,
            "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None,
            "scaler_state_dict": self.trainer.scaler.state_dict() if self.trainer.scaler else None,
            "rng_state": torch.get_rng_state(),
            "config": self.config,
            "best_val_loss": self.best_val_loss,
            "val_loss": val_loss
        }
        
        path = save_checkpoint(
            state,
            self.config.output_dir,
            filename=filename,
            keep_last_n=getattr(self.config, "keep_last_n_checkpoints", 3)
        )
        
        if step_filename:
            save_checkpoint(
                state,
                self.config.output_dir,
                filename=step_filename,
                keep_last_n=getattr(self.config, "keep_last_n_checkpoints", 3)
            )
            
        return path

    def load_state(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Loads state from checkpoint file.
        """
        checkpoint = load_checkpoint(
            filepath,
            self.model,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
            scaler=self.trainer.scaler,
            device=getattr(self.config, "device", "cpu")
        )
        self.trainer.global_step = checkpoint.get("global_step", 0)
        self.best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        return checkpoint
