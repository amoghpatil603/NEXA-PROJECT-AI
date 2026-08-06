# Model Design Specification

## Configuration System
The `NexaFMConfig` defines the architectural hyperparameters, allowing us to instantiate multiple model sizes from the same codebase without duplication.

### Parameters
- `vocab_size`: 50257 (default)
- `hidden_size`: Dimensionality of the embeddings and hidden states.
- `num_layers`: Number of Transformer blocks.
- `num_heads`: Number of attention heads.
- `max_context_length`: Maximum sequence length (e.g., 4096).
- `activation_function`: Default to `gelu`.
- `dropout_prob`: 0.1
- `initializer_range`: 0.02
- `layer_norm_eps`: 1e-5
- `use_rotary_embeddings`: True

### Scalable Profiles
- **Small**: 512 hidden size, 8 layers, 8 heads.
- **Base**: 768 hidden size, 12 layers, 12 heads.
- **Large**: 1536 hidden size, 24 layers, 16 heads.

## Module Layout
The model architecture resides in `backend/models/nexa_fm/`:
- `__init__.py`: Exposes `NexaFMConfig` and `NexaFMModel`.
- `config.py`: Contains the dataclass definitions.
- `architecture.py`: Contains the PyTorch implementation of the decoder-only Transformer.

## Integration Plan
- **FastAPI / Chat**: The model will be instantiated by `ChatEngine`, receiving tokenized input and outputting logits for sampling. 
- **WebSockets / Streaming**: The generation loop will yield tokens incrementally, which the FastAPI WebSocket layer will stream back to the UI.
- **Memory & RAG**: Context will be injected into the `system_prompt` or user prompt, dynamically expanding the sequence up to `max_context_length`.
- **Studio**: The UI will query the active `NexaFMConfig` via a `/metrics` or `/model_info` endpoint to display Context Length, Hidden Size, and Layer Count.
