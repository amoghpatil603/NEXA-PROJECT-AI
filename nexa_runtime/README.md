# NEXA Runtime SDK

The foundational infrastructure for the NEXA ecosystem, providing a modular, provider-agnostic AI engine.

## Architecture
- **core/**: Lifecycle management via `RuntimeManager`.
- **loaders/**: Checkpoint discovery and validation via `ModelLoader`.
- **engine/**: Standardized `InferenceEngine` base classes.
- **providers/**: Backend-specific execution (Local, Gemini).
- **services/**: Agentic capabilities (RAG, Memory, Tool Calling).

## Usage
```python
from nexa_runtime import NexaRuntime

sdk = NexaRuntime()
sdk.start()
call = sdk.generate("Mission Status?")
