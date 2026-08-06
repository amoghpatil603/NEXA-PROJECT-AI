# Training Roadmap

## Phase 1: Architecture Validation (Current)
- Design the decoder-only Transformer.
- Establish the configuration profiles.
- Ensure the code gracefully handles environments without PyTorch (returning `501 Not Implemented`).

## Phase 2: Data Pipeline Construction
- Build robust tokenization pipelines.
- Curate and preprocess pre-training datasets (web scrape, books, code).
- Implement efficient dataloaders for distributed training.

## Phase 3: Pre-Training
- Initialize weights across the cluster.
- Train the `base` profile to establish learning rate schedules.
- Scale up to the `large` profile.

## Phase 4: Supervised Fine-Tuning (SFT)
- Curate high-quality instruction-following datasets.
- Fine-tune the pre-trained checkpoints for conversational AI and tool usage.

## Phase 5: RLHF / Alignment
- Train a reward model.
- Apply PPO (Proximal Policy Optimization) or DPO (Direct Preference Optimization) to align the model with human preferences for safety and helpfulness.

## Phase 6: Production Deployment
- Convert final PyTorch weights to optimized formats (e.g., ONNX, GGUF, or Safetensors).
- Deploy to the `checkpoints/` directory.
- Enable full inference across Chat, Memory, RAG, Vision, and Voice integrations.
