import math
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    torch = None
    nn = None
    F = None

from .config import NexaFMConfig

if torch is not None:
    class RotaryPositionalEmbedding(nn.Module):
        def __init__(self, dim, max_seq_len=4096):
            super().__init__()
            inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
            self.register_buffer("inv_freq", inv_freq)
            self.max_seq_len = max_seq_len
            
        def forward(self, x, seq_len):
            t = torch.arange(seq_len, device=x.device, dtype=self.inv_freq.dtype)
            freqs = torch.einsum("i,j->ij", t, self.inv_freq)
            emb = torch.cat((freqs, freqs), dim=-1)
            return emb

    def apply_rotary_pos_emb(x, sin, cos):
        return (x * cos) + (rotate_half(x) * sin)

    def rotate_half(x):
        x1, x2 = x[..., :x.shape[-1]//2], x[..., x.shape[-1]//2:]
        return torch.cat((-x2, x1), dim=-1)

    class MultiHeadSelfAttention(nn.Module):
        def __init__(self, config: NexaFMConfig):
            super().__init__()
            self.num_heads = config.num_heads
            self.head_dim = config.hidden_size // config.num_heads
            
            self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
            self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
            self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
            self.out_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=False)
            
            self.dropout = nn.Dropout(config.dropout_prob)
            self.use_rotary = config.use_rotary_embeddings
            if self.use_rotary:
                self.rotary_emb = RotaryPositionalEmbedding(self.head_dim, config.max_context_length)

        def forward(self, hidden_states, attention_mask=None):
            batch_size, seq_len, _ = hidden_states.shape
            
            q = self.q_proj(hidden_states).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            k = self.k_proj(hidden_states).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            v = self.v_proj(hidden_states).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            
            if self.use_rotary:
                pos_emb = self.rotary_emb(hidden_states, seq_len)
                cos, sin = pos_emb.cos(), pos_emb.sin()
                q = apply_rotary_pos_emb(q, sin, cos)
                k = apply_rotary_pos_emb(k, sin, cos)
            
            scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
            
            if attention_mask is not None:
                scores = scores + attention_mask
                
            attn_weights = F.softmax(scores, dim=-1)
            attn_weights = self.dropout(attn_weights)
            
            context = torch.matmul(attn_weights, v)
            context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)
            
            return self.out_proj(context)

    class FeedForward(nn.Module):
        def __init__(self, config: NexaFMConfig):
            super().__init__()
            self.fc1 = nn.Linear(config.hidden_size, config.hidden_size * 4)
            self.fc2 = nn.Linear(config.hidden_size * 4, config.hidden_size)
            self.act = nn.GELU() if config.activation_function == "gelu" else nn.ReLU()
            self.dropout = nn.Dropout(config.dropout_prob)

        def forward(self, x):
            return self.dropout(self.fc2(self.act(self.fc1(x))))

    class NexaFMBlock(nn.Module):
        def __init__(self, config: NexaFMConfig):
            super().__init__()
            self.ln_1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
            self.attn = MultiHeadSelfAttention(config)
            self.ln_2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
            self.mlp = FeedForward(config)

        def forward(self, x, attention_mask=None):
            x = x + self.attn(self.ln_1(x), attention_mask=attention_mask)
            x = x + self.mlp(self.ln_2(x))
            return x

    class NexaFMModel(nn.Module):
        def __init__(self, config: NexaFMConfig):
            super().__init__()
            self.config = config
            self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
            
            self.use_rotary = config.use_rotary_embeddings
            if not self.use_rotary:
                self.embed_positions = nn.Embedding(config.max_context_length, config.hidden_size)
                
            self.layers = nn.ModuleList([NexaFMBlock(config) for _ in range(config.num_layers)])
            self.ln_f = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
            self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
            
            # Weight tie
            self.lm_head.weight = self.embed_tokens.weight

        def forward(self, input_ids, attention_mask=None):
            b, t = input_ids.shape
            x = self.embed_tokens(input_ids)
            
            if not self.use_rotary:
                positions = torch.arange(0, t, dtype=torch.long, device=input_ids.device)
                x = x + self.embed_positions(positions)
                
            if attention_mask is not None:
                # Add causal mask logic if provided
                pass
                
            for layer in self.layers:
                x = layer(x, attention_mask=attention_mask)
                
            x = self.ln_f(x)
            logits = self.lm_head(x)
            return logits

else:
    class NexaFMModel:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is required to instantiate NexaFMModel")
