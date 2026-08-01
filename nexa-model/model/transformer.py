import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from .config import NexaConfig
from .block import Block

class NexaTransformer(nn.Module):
    def __init__(self, config: NexaConfig):
        super().__init__()
        self.config = config
        self.transformer = nn.ModuleDict(dict(
            wte = nn.Embedding(config.vocab_size, config.d_model),
            wpe = nn.Embedding(config.max_seq_len, config.d_model),
            drop = nn.Dropout(config.dropout),
            h = nn.ModuleList([Block(config) for _ in range(config.n_layers)]),
            ln_f = nn.LayerNorm(config.d_model, eps=config.norm_eps, bias=config.bias),
        ))
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        
        if config.weight_tying:
            self.lm_head.weight = self.transformer.wte.weight

        self.apply(self._init_weights)
        
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            
    def forward(self, idx, targets=None):
        B, T = idx.size()
        assert T <= self.config.max_seq_len, f"Cannot forward sequence of length {T}, max {self.config.max_seq_len}"
        pos = torch.arange(0, T, dtype=torch.long, device=idx.device)
        
        tok_emb = self.transformer.wte(idx)
        pos_emb = self.transformer.wpe(pos)
        x = self.transformer.drop(tok_emb + pos_emb)
        for block in self.transformer.h:
            x = block(x)
        x = self.transformer.ln_f(x)
        
        if targets is not None:
            logits = self.lm_head(x)
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-100)
            return logits, loss
        else:
            logits = self.lm_head(x[:, [-1], :]) 
            return logits, None
