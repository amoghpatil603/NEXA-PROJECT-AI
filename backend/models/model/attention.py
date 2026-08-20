import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from .config import NexaConfig

class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_seq_len: int = 2048, base: int = 10000):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self.max_seq_len = max_seq_len
        self._set_cos_sin_cache(max_seq_len)

    def _set_cos_sin_cache(self, seq_len: int):
        t = torch.arange(seq_len, dtype=self.inv_freq.dtype)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :], persistent=False)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, x, seq_len: int):
        return (
            self.cos_cached[:, :, :seq_len, :].to(x.device),
            self.sin_cached[:, :, :seq_len, :].to(x.device)
        )

def rotate_half(x):
    x1 = x[..., :x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2:]
    return torch.cat((-x2, x1), dim=-1)

def apply_rotary_pos_emb(q, k, cos, sin):
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed

class CausalSelfAttention(nn.Module):
    def __init__(self, config: NexaConfig):
        super().__init__()
        assert config.d_model % config.n_heads == 0
        self.c_attn = nn.Linear(config.d_model, 3 * config.d_model, bias=config.bias)
        self.c_proj = nn.Linear(config.d_model, config.d_model, bias=config.bias)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.n_heads = config.n_heads
        self.d_model = config.d_model
        self.head_dim = config.d_model // config.n_heads

        pos_type = getattr(config, "pos_type", "rope").lower()
        self.is_rope = (pos_type == "rope")
        if self.is_rope:
            self.rotary_emb = RotaryEmbedding(self.head_dim, max_seq_len=config.max_seq_len)

        self.register_buffer(
            "bias",
            torch.tril(torch.ones(config.max_seq_len, config.max_seq_len)).view(1, 1, config.max_seq_len, config.max_seq_len)
        )

    def forward(self, x, layer_past=None, attention_mask=None):
        B, T, C = x.size()
        qkv = self.c_attn(x)
        q, k, v = qkv.split(self.d_model, dim=2)
        q = q.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)

        if layer_past is not None and layer_past[0] is not None:
            past_k, past_v = layer_past
            past_len = past_k.size(-2)
            max_buf_len = self.bias.size(-1)
            if past_len + T > max_buf_len:
                keep_len = max(0, max_buf_len - T)
                past_k = past_k[:, :, -keep_len:, :]
                past_v = past_v[:, :, -keep_len:, :]
                past_len = keep_len
            total_len = past_len + T
            if self.is_rope:
                cos, sin = self.rotary_emb(v, total_len)
                cos = cos[:, :, past_len:total_len, :]
                sin = sin[:, :, past_len:total_len, :]
                q, k = apply_rotary_pos_emb(q, k, cos, sin)
            k = torch.cat([past_k, k], dim=-2)
            v = torch.cat([past_v, v], dim=-2)
        else:
            total_len = T
            past_len = 0
            if self.is_rope:
                cos, sin = self.rotary_emb(v, T)
                q, k = apply_rotary_pos_emb(q, k, cos, sin)

        present = (k, v)

        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(self.head_dim))
        if attention_mask is not None:
            if attention_mask.dtype == torch.bool:
                att = att.masked_fill(~attention_mask, float('-inf'))
            else:
                att = att.masked_fill(attention_mask == 0, float('-inf'))
        elif layer_past is not None and T == 1:
            pass
        else:
            mask = self.bias[:, :, past_len:total_len, :total_len]
            att = att.masked_fill(mask == 0, float('-inf'))

        att = torch.nan_to_num(F.softmax(att, dim=-1), 0.0)
        att = self.attn_dropout(att)

        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.resid_dropout(self.c_proj(y))
        return y, present
