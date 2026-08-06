# NEXA Platform - Model Dependency Report

## Missing Dependencies and Models

The following critical dependencies are currently missing from the production environment, preventing the AI inference pipelines from initializing:

1. **PyTorch (`torch`)**: Not installed in the production environment.
2. **NEXA Model Architecture (`nexa-model` directory)**: The core modules `model.config`, `model.transformer`, and `tokenizer` are missing.
3. **NEXA Checkpoint (`checkpoints/model.pt`)**: The trained model weights are absent.
4. **Voice Processing Dependencies**: There are no Speech-to-Text or Text-to-Speech models or engines installed (e.g., `pyttsx3`, `speech_recognition`).

## Impact

- `/chat` endpoint: Will return a `501 Not Implemented` error.
- `/voice` endpoint: Will return a `501 Not Implemented` error.
- Background Jobs / ExecutionEngine: Any logic relying on `ChatEngine` will raise an explicit failure rather than silently proceeding with mocked outputs.

## Remediation Requirements

To fully activate the NEXA Platform AI features, the deployment environment must be provisioned with the required PyTorch wheels, the `nexa-model` source directory must be pulled, and the `.pt` checkpoints must be placed in the `/checkpoints` volume.
