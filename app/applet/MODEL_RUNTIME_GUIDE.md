# Model Runtime Integration Guide

## Introduction
This guide outlines how to correctly integrate the physical model assets into the NEXA Platform once they become available. The system is designed to automatically detect and mount the AI engines once the required structural dependencies are fulfilled.

## Expected Directory Structure
Ensure the repository contains the following architecture prior to boot:

```
/app/applet/
├── checkpoints/
│   └── model.pt              # The required PyTorch weights (or equivalent GGUF/Safetensors)
├── backend/
│   ├── models/
│   │   ├── chat_engine.py    # Existing integration point
│   │   └── model/            # REQUIRED: The core model architecture
│   │       ├── config.py
│   │       ├── transformer.py
│   │       └── ...
│   └── tokenizer/            # REQUIRED: Tokenization algorithms
```

## Integrating the Models
1. **Model Architecture**: The system relies on custom model architecture classes (e.g., `NexaTransformer` and `NexaConfig`). These must be placed in a discoverable Python path.
2. **Weight Checkpoints**: Place the primary trained weights at `/app/applet/checkpoints/model.pt`.
3. **Dependencies**: Ensure `torch` and any necessary C++ inference bindings (e.g., `llama-cpp-python` if using GGUF in the future) are installed in the deployment environment.

## Activating Inference
Once the models and weights are present:
1. The FastAPI service (`backend/api/ai_service.py`) will automatically initialize `ChatEngine` on startup.
2. If successful, the `/health` endpoint will transition `model_loaded` to `true`.
3. The HTTP `/chat` and WebSocket pipelines will seamlessly transition from emitting `501 Not Implemented` to streaming genuine inference tokens back to the client UI.

## Safety Constraints
- **Never mock inference**: If the weights are corrupt or missing, the system must fail to start or safely return a 501.
- **Never hardcode outputs**: All streamed chunks must originate from the `engine.stream_generate` generator.
