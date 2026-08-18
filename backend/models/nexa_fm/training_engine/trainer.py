import torch
import torch.nn as nn
import torch.nn.functional as F

class Trainer:
    def __init__(self, model, config, dataloader):
        self.model = model
        self.config = config
        self.dataloader = dataloader
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=config.learning_rate)
        self.scaler = torch.cuda.amp.GradScaler(enabled=config.mixed_precision and self.device == 'cuda')

    def train():
        self.model.train()
        for batch in self.dataloader:
            batch = batch.to(self.device)
            with torch.cuda.amp.autocast(enabled=self.config.mixed_precision):
                logits = self.model(batch)
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = batch[..., 1:].contiguous()
                loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            
            self.scaler.scale(loss / self.config.gradient_accumulation_steps).backward()
            # ... standard optimizer step logic ...
