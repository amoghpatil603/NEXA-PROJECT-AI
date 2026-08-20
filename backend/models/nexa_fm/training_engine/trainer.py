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
        
        if torch and hasattr(torch, "amp") and hasattr(torch.amp, "GradScaler"):
            try:
                self.scaler = torch.amp.GradScaler('cuda', enabled=self.config.mixed_precision and self.device.type == 'cuda')
            except Exception:
                self.scaler = torch.cuda.amp.GradScaler(enabled=self.config.mixed_precision and self.device.type == 'cuda') if hasattr(torch, "cuda") and hasattr(torch.cuda, "amp") and hasattr(torch.cuda.amp, "GradScaler") else None
        elif torch and hasattr(torch, "cuda") and hasattr(torch.cuda, "amp") and hasattr(torch.cuda.amp, "GradScaler"):
            self.scaler = torch.cuda.amp.GradScaler(enabled=self.config.mixed_precision and self.device.type == 'cuda')
        else:
            self.scaler = None
        
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
                latest, self.model, self.optimizer, self.scheduler, self.dataloader, self.scaler, config=self.config
            )

    def train(self):
        self.model.train()

        print(f"Starting training on {self.device}")

        if torch is None or self.optimizer is None:
            if os.environ.get("NEXA_RUN_MOCK_TRAINING") == "1":
                print("Torch optimizer unavailable. Running simulated loop.")
                self._simulated_loop()
                return
            raise RuntimeError("Required ML runtime (PyTorch/Optimizer) is unavailable for production training.")

        data_iter = iter(self.dataloader)
        self.optimizer.zero_grad()

        try:
            while self.optimizer_step < self.config.max_steps:
                try:
                    batch = next(data_iter)
                except StopIteration:
                    self.epoch += 1
                    data_iter = iter(self.dataloader)
                    try:
                        batch = next(data_iter)
                    except StopIteration:
                        print("Dataloader is empty. Stopping.")
                        break

                if hasattr(batch, "to"):
                    batch = batch.to(self.device)
                elif isinstance(batch, dict):
                    batch = {k: v.to(self.device) for k, v in batch.items()}
                elif isinstance(batch, (list, tuple)):
                    batch = batch[0].to(self.device) if hasattr(batch[0], "to") else batch[0]

                # Forward pass with proper autocast context
                autocast_context = torch.autocast(device_type=self.device.type, enabled=self.config.mixed_precision and self.device.type == 'cuda') if hasattr(torch, "autocast") else contextlib.nullcontext()

                with autocast_context:
                    # For standard causal LM, inputs and labels are the same
                    if isinstance(batch, dict):
                        outputs = self.model(**batch)
                        labels = batch.get("labels", batch.get("input_ids"))
                    else:
                        try:
                            outputs = self.model(batch, targets=batch)
                        except TypeError:
                            outputs = self.model(batch)
                        labels = batch

                    if hasattr(outputs, 'loss') and outputs.loss is not None:
                        loss = outputs.loss
                    elif isinstance(outputs, (tuple, list)):
                        if len(outputs) > 1 and outputs[1] is not None and isinstance(outputs[1], torch.Tensor) and outputs[1].numel() == 1:
                            loss = outputs[1]
                        elif isinstance(outputs[0], torch.Tensor) and outputs[0].numel() == 1:
                            loss = outputs[0]
                        else:
                            logits = outputs[0]
                            shift_logits = logits[..., :-1, :].contiguous()
                            shift_labels = labels[..., 1:].contiguous()
                            import torch.nn.functional as F
                            loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                    else:
                        # Handle raw tensor outputs (logits)
                        logits = outputs
                        shift_logits = logits[..., :-1, :].contiguous()
                        shift_labels = labels[..., 1:].contiguous()
                        import torch.nn.functional as F
                        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                    loss = loss / self.config.gradient_accumulation_steps

                # Backward pass
                if self.scaler:
                    self.scaler.scale(loss).backward()
                else:
                    loss.backward()

                self.micro_step += 1

                if self.micro_step % self.config.gradient_accumulation_steps == 0:
                    if self.scaler:
                        self.scaler.unscale_(self.optimizer)

                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)

                    if self.scaler:
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                    else:
                        self.optimizer.step()

                    self.scheduler.step()
                    self.optimizer.zero_grad()

                    self.optimizer_step += 1

                    if self.optimizer_step % self.config.log_steps == 0:
                        self.logger.log({
                            "step": self.optimizer_step,
                            "micro_step": self.micro_step,
                            "epoch": self.epoch,
                            "loss": loss.item() * self.config.gradient_accumulation_steps,
                            "lr": self.scheduler.get_last_lr()[0]
                        })

                    if self.optimizer_step % self.config.save_steps == 0 and self.optimizer_step > 0:
                        self.checkpoint_manager.save(
                            model=self.model,
                            optimizer=self.optimizer,
                            scheduler=self.scheduler,
                            step=self.optimizer_step,
                            micro_step=self.micro_step,
                            epoch=self.epoch,
                            dataloader=self.dataloader,
                            config=self.config,
                            scaler=self.scaler
                        )
        except KeyboardInterrupt:
            print(f"\n[Trainer] Training gracefully interrupted by user at step {self.optimizer_step}.")
            if self.optimizer_step > 0:
                print(f"[Trainer] Preserving safe checkpoint at step {self.optimizer_step}...")
                self.checkpoint_manager.save(
                    model=self.model,
                    optimizer=self.optimizer,
                    scheduler=self.scheduler,
                    step=self.optimizer_step,
                    micro_step=self.micro_step,
                    epoch=self.epoch,
                    dataloader=self.dataloader,
                    config=self.config,
                    scaler=self.scaler
                )
                print("[Trainer] Safe checkpoint saved successfully. Exiting cleanly.")

    def resume_from_checkpoint(self, checkpoint_path=None) -> bool:
        """
        Discovers the latest valid checkpoint automatically if not specified,
        restores model, optimizer, scheduler, scaler, RNG, dataloader cursor,
        and enforces all identity guards.
        """
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_manager.get_latest_checkpoint()

        if checkpoint_path is None or not os.path.exists(checkpoint_path):
            print("No existing valid checkpoint found. Starting fresh training run.")
            return False

        print(f"Discovered checkpoint: {checkpoint_path}. Restoring training state...")
        step, micro_step, epoch = self.checkpoint_manager.load(
            path=checkpoint_path,
            model=self.model,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
            dataloader=self.dataloader,
            scaler=self.scaler,
            config=self.config
        )
        self.optimizer_step = step
        self.micro_step = micro_step
        self.epoch = epoch
        print(f"Successfully resumed from checkpoint at step {self.optimizer_step} (micro_step {self.micro_step}, epoch {self.epoch}).")
        return True

    def _simulated_loop(self):
        # Used for testing environments where torch fails to run real optimization
        self.optimizer_step += 1
        self.micro_step += self.config.gradient_accumulation_steps
        self.logger.log({"step": self.optimizer_step, "epoch": self.epoch, "loss": 0.5, "lr": 1e-4})
        self.checkpoint_manager.save(self.model, self.optimizer, self.scheduler, self.optimizer_step, self.micro_step, self.epoch, self.dataloader, self.config, self.scaler)

    def dry_run(self):
        print(f"Starting dry-run validation on {self.device}")
        try:
            self.model.train()
        except:
            pass
        try:
            data_iter = iter(self.dataloader)
            batch = next(data_iter)
            if hasattr(batch, "to"):
                batch = batch.to(self.device)
            elif isinstance(batch, dict):
                batch = {k: v.to(self.device) for k, v in batch.items()}
            elif isinstance(batch, (list, tuple)):
                batch = batch[0].to(self.device) if hasattr(batch[0], "to") else batch[0]

            print("Successfully loaded batch from DataLoader.")
        except Exception as e:
            print(f"Failed to load batch: {e}")
            return False

        if self.optimizer is None:
            print("Torch optimizer unavailable. Dry-run limited.")
            return True

        try:
            # Forward pass
            print("Running forward pass...")
            with torch.autocast(device_type=self.device.type, enabled=self.config.mixed_precision and self.device.type == 'cuda') if hasattr(torch, "autocast") else torch.no_grad():
                if isinstance(batch, dict):
                    outputs = self.model(**batch)
                    labels = batch.get("labels", batch.get("input_ids"))
                else:
                    try:
                        outputs = self.model(batch, targets=batch)
                    except TypeError:
                        outputs = self.model(batch)
                    labels = batch

                if hasattr(outputs, "loss") and outputs.loss is not None:
                    loss = outputs.loss
                elif isinstance(outputs, (tuple, list)):
                    if len(outputs) > 1 and outputs[1] is not None and isinstance(outputs[1], torch.Tensor) and outputs[1].numel() == 1:
                        loss = outputs[1]
                    elif isinstance(outputs[0], torch.Tensor) and outputs[0].numel() == 1:
                        loss = outputs[0]
                    else:
                        logits = outputs[0]
                        shift_logits = logits[..., :-1, :].contiguous()
                        shift_labels = labels[..., 1:].contiguous()
                        import torch.nn.functional as F
                        loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                else:
                    # outputs are logits
                    logits = outputs
                    shift_logits = logits[..., :-1, :].contiguous()
                    shift_labels = labels[..., 1:].contiguous()
                    import torch.nn.functional as F
                    loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

            print(f"Computed loss: {loss.item() if hasattr(loss, 'item') else loss}")

            # Backward pass
            print("Running backward pass...")
            if self.scaler:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            print("Successfully ran backward pass.")

            # Step
            if self.scaler:
                self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            if self.scaler:
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.optimizer.step()
            self.scheduler.step()
            self.optimizer.zero_grad()
            print("Successfully updated weights. Dry-run validation complete.")
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Dry-run failed during model execution: {e}")
            return False
            

