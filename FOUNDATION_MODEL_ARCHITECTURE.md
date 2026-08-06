# Foundation Model Architecture

## Architecture Overview
The NEXA Foundation Model is based on a **decoder-only Transformer** architecture, optimized for sequential auto-regressive generation. 

## Key Components

### 1. Embeddings & Positional Encoding
- **Token Embeddings**: A standard `nn.Embedding` layer mapping the input vocabulary (size 50,257) to the hidden size.
- **Positional Encodings**: We utilize **Rotary Positional Embeddings (RoPE)**. 
  - **Justification**: RoPE provides superior length extrapolation properties compared to absolute or relative positional encodings. It naturally models relative distances while maintaining the efficiency of absolute encodings, which is crucial for dynamic context lengths (e.g., chat and RAG interactions).

### 2. Multi-Head Self-Attention
- **Mechanism**: Standard multi-head self attention with query, key, and value projections.
- **Rotary Application**: RoPE is applied directly to the query and key vectors before computing the attention scores.
- **Causal Masking**: Ensures tokens can only attend to previous tokens.

### 3. Feed-Forward Block
- **Structure**: A two-layer MLP expanding the hidden size by a factor of 4, followed by a non-linear activation, and projecting back to the hidden size.
- **Activation**: **GELU** (Gaussian Error Linear Unit) is used by default for smooth derivatives and empirically better performance than ReLU.

### 4. Normalization & Residuals
- **Pre-Normalization Strategy**: `LayerNorm` is applied *before* the attention and feed-forward sub-layers.
- **Residual Connections**: Standard `x = x + sublayer(LayerNorm(x))` approach to ensure stable gradients during deep network training.

### 5. Output Projection
- **Weight Tying**: The final language modeling head (`lm_head`) shares its weights with the input token embeddings (`embed_tokens.weight`). This reduces the total parameter count and acts as a regularizer.
- **Final Norm**: A final `LayerNorm` is applied before the projection to logits.
