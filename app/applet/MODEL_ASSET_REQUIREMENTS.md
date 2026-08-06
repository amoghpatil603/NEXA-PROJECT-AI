# NEXA Platform - Model Asset Requirements

## Executive Summary
The NEXA Platform requires a physical model runtime and associated weight assets to perform inference operations. An audit of the repository reveals that there are no model files (GGUF, PyTorch, Safetensors, ONNX, etc.) or a valid `nexa-model` runtime package present in the deployment environment. 

## Missing Assets

The following files and directories are completely missing from the project root and are strictly required before inference can be instantiated:

### 1. Model Weights
- **Formats Expected**: `.pt`, `.ckpt`, `.gguf`, or `.safetensors`
- **Location**: `/app/applet/checkpoints/`
- **Impact**: Without valid weight files, the inference engine cannot initialize. The system is designed to halt to prevent returning random or mocked outputs.

### 2. Runtime Architecture (`nexa-model` directory)
- **Files Expected**: The core modeling classes such as `model.config`, `model.transformer`, and `training.checkpoint`.
- **Location**: `/app/applet/nexa-model/` or as an installable Python package.
- **Impact**: The `backend/models/chat_engine.py` script attempts to import from `model.config` and `model.transformer`, which are structurally absent.

### 3. Voice and Vision Models (Optional but required for full features)
- **Voice Models**: Missing any speech recognition (STT) or Text-to-Speech (TTS) models (e.g., Whisper weights).
- **Vision Models**: Missing OCR engines (e.g., Tesseract data files) or multimodal encoders.

## Next Steps

To proceed with v1.2.0 production deployment:
1. Download the approved NEXA `.pt` or `.gguf` weights.
2. Place the weights inside the `checkpoints/` directory.
3. Import the exact `nexa-model` Python package containing the model class architecture.

Once the assets are correctly placed, the `ChatEngine` will successfully load and the API endpoints will transition out of their `501 Not Implemented` state.
