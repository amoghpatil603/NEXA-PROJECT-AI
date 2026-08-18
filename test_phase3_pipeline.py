import sys
import os
import shutil
import torch
from pathlib import Path

sys.path.insert(0, "nexa-model")

from model.config import NexaConfig
from model.transformer import NexaTransformer
from training.config import TrainingConfig
from training.optimizer import configure_optimizers
from training.scheduler import get_cosine_schedule_with_warmup
from training.train_loop import TrainLoop
from training.checkpoint import load_checkpoint

def run_phase3_verification():
    print("====================================================")
    print("STARTING NEXA-1 TINY TRAINING PIPELINE VERIFICATION")
    print("====================================================")

    test_dir = Path("test_checkpoints_phase3")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    # 1. Instantiate 50M Model Architecture (NEXA-1 Tiny)
    model_config = NexaConfig.tiny()
    model_config.gradient_checkpointing = True
    model = NexaTransformer(model_config)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Model Initialized: {model.__class__.__name__}")
    print(f"   Parameters: {total_params:,}")
    print(f"   Architecture: d_model={model_config.d_model}, layers={model_config.n_layers}, heads={model_config.n_heads}, d_ff={model_config.d_ff}")
    print(f"   Features: SwiGLU={model_config.activation=='swiglu'}, RoPE={model_config.pos_type=='rope'}, RMSNorm={model_config.norm_type=='rmsnorm'}, Activation Checkpointing={model_config.gradient_checkpointing}")

    assert 48_000_000 <= total_params <= 51_000_000, f"Parameter count {total_params} out of range!"

    # 2. Setup Dummy Synthetic Dataset for Verification
    batch_size = 2
    seq_len = 64
    train_data = [(torch.randint(0, model_config.vocab_size, (batch_size, seq_len)),
                   torch.randint(0, model_config.vocab_size, (batch_size, seq_len))) for _ in range(10)]
    val_data = [(torch.randint(0, model_config.vocab_size, (batch_size, seq_len)),
                 torch.randint(0, model_config.vocab_size, (batch_size, seq_len))) for _ in range(3)]

    # 3. Setup Training Configuration
    train_config = TrainingConfig(
        learning_rate=1e-3,
        gradient_accumulation_steps=2,
        micro_batch_size=batch_size,
        context_len=seq_len,
        precision="auto",
        gradient_checkpointing=True,
        output_dir=str(test_dir),
        eval_every_steps=2,
        save_every_steps=2,
        log_every_steps=1,
        keep_last_n_checkpoints=2,
        device="cpu"
    )

    optimizer = configure_optimizers(model, weight_decay=train_config.weight_decay, learning_rate=train_config.learning_rate)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps=2, max_steps=10)

    # 4. Instantiate TrainLoop & Execute 2 Steps
    train_loop = TrainLoop(
        model=model,
        train_dataloader=train_data,
        val_dataloader=val_data,
        optimizer=optimizer,
        scheduler=scheduler,
        config=train_config
    )

    print("\nExecuting Training Steps...")
    train_loop.run(max_steps=2)

    # 5. Verify Checkpoint Generation
    latest_ckpt = test_dir / "latest.ckpt"
    best_ckpt = test_dir / "best.ckpt"
    latest_json = test_dir / "latest.json"

    assert latest_ckpt.exists(), "latest.ckpt was not generated!"
    assert best_ckpt.exists(), "best.ckpt was not generated!"
    assert latest_json.exists(), "latest.json sidecar was not generated!"

    print("✅ Checkpoint Saving & Sidecar Verification Passed")

    # 6. Verify Checkpoint Resume
    resume_model = NexaTransformer(model_config)
    resume_optimizer = configure_optimizers(resume_model, weight_decay=train_config.weight_decay, learning_rate=train_config.learning_rate)
    loaded_state = load_checkpoint(latest_ckpt, resume_model, resume_optimizer, device="cpu")

    assert loaded_state["global_step"] == 2, f"Expected step 2, got {loaded_state['global_step']}"
    print("✅ Checkpoint Resuming Verification Passed")

    # 7. Cleanup
    shutil.rmtree(test_dir)
    print("\n====================================================")
    print("NEXA-1 TINY TRAINING PIPELINE VERIFICATION PASSED SUCCESSFULLY")
    print("====================================================")

if __name__ == "__main__":
    run_phase3_verification()
