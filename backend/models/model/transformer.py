import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from .config import NexaConfig
from .block import Block
from .norm import RMSNorm

class NexaTransformer(nn.Module):
    def __init__(self, config: NexaConfig):
        super().__init__()
        self.config = config

        norm_type = getattr(config, "norm_type", "layernorm").lower()
        pos_type = getattr(config, "pos_type", "rope").lower()
        self.is_rope = (pos_type == "rope")

        transformer_dict = dict(
            wte = nn.Embedding(config.vocab_size, config.d_model),
            drop = nn.Dropout(config.dropout),
            h = nn.ModuleList([Block(config) for _ in range(config.n_layers)]),
        )

        if not self.is_rope:
            transformer_dict["wpe"] = nn.Embedding(config.max_seq_len, config.d_model)

        if norm_type == "rmsnorm":
            transformer_dict["ln_f"] = RMSNorm(config.d_model, eps=config.norm_eps)
        else:
            transformer_dict["ln_f"] = nn.LayerNorm(config.d_model, eps=config.norm_eps)

        self.transformer = nn.ModuleDict(transformer_dict)
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

    def forward(self, idx, targets=None, past_key_values=None, use_cache=False):
        B, T = idx.size()
        max_seq_len = self.config.max_seq_len

        # If input exceeds max_seq_len, truncate to last max_seq_len tokens
        if T > max_seq_len:
            idx = idx[:, -max_seq_len:]
            T = max_seq_len
            past_key_values = None

        if past_key_values is not None and len(past_key_values) > 0 and past_key_values[0] is not None and past_key_values[0][0] is not None:
            past_len = past_key_values[0][0].size(-2)
            if past_len + T > max_seq_len:
                keep_len = max(0, max_seq_len - T)
                if keep_len > 0:
                    past_key_values = tuple(
                        (k[:, :, -keep_len:, :], v[:, :, -keep_len:, :])
                        for (k, v) in past_key_values
                    )
                    past_len = keep_len
                else:
                    past_key_values = None
                    past_len = 0
        else:
            past_len = 0

        total_len = past_len + T

        tok_emb = self.transformer.wte(idx)
        if not self.is_rope:
            pos = torch.arange(past_len, total_len, dtype=torch.long, device=idx.device)
            pos_emb = self.transformer.wpe(pos)
            x = self.transformer.drop(tok_emb + pos_emb)
        else:
            x = self.transformer.drop(tok_emb)

        presents = [] if use_cache else None
        for i, block in enumerate(self.transformer.h):
            layer_past = past_key_values[i] if past_key_values is not None else None
            x, present = block(x, layer_past=layer_past)
            if use_cache:
                presents.append(present)

        x = self.transformer.ln_f(x)

        if targets is not None:
            logits = self.lm_head(x)
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-100)
            if use_cache:
                return logits, loss, tuple(presents)
            return logits, loss
        else:
            logits = self.lm_head(x[:, [-1], :])
            if use_cache:
                return logits, tuple(presents)
            return logits, None
