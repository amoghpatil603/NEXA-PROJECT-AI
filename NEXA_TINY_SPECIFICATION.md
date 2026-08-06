# NEXA Tiny - Model Specification

## Purpose
NEXA Tiny is a research-scale configuration designed explicitly for end-to-end pipeline validation, integration testing, and dry-run execution. It is purposefully small to ensure rapid initialization and debugging without extensive computational overhead.

## Architecture Configuration
- **hidden_size**: 128
- **num_layers**: 4
- **num_heads**: 4
- **max_context_length**: 128
- **vocab_size**: 50257 (Aligned with BPE Tokenizer)

## Design Decisions
- **Modularity**: Completely separated from the primary Small/Base/Large scales to prevent accidental usage in production contexts.
- **Resource Constraints**: Can be executed entirely on CPU for quick integration tests.

## Usage
To instantiate this model config programmatically:
```python
from backend.models.nexa_fm.config import NexaFMConfig
config = NexaFMConfig.tiny()
```
