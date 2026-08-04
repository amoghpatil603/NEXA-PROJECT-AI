import sys
import os
import time
import shutil
import resource
import torch
torch.set_num_threads(1)
from pathlib import Path

# Add nexa-model to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "nexa-model"))

from model.config import NexaConfig
from model.transformer import NexaTransformer
from training.optimizer import configure_optimizers
from training.scheduler import get_cosine_schedule_with_warmup
from training.checkpoint import save_checkpoint, load_checkpoint


def run_quick_verification():
    start_time = time.time()
    results = {}
    print("====================================================")
    print("NEXA PHASE 3 LIGHTWEIGHT QUICK VERIFICATION SUITE")
    print("====================================================")

    test_dir = Path("test_checkpoints_phase3_quick")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Verify Model Initialization (NEXA-1 Tiny ~50M params)
        print("[1/9] Verifying Model Initialization (NEXA-1 Tiny)...")
        model_config = NexaConfig.tiny()
        model_config.gradient_checkpointing = False
        model = NexaTransformer(model_config)
        model.train()

        param_count = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        assert 48_000_000 <= param_count <= 51_000_000, f"Parameter count {param_count} out of expected ~50M range"
        results["parameter_count"] = param_count
        print(f"  ✅ Model initialized: {param_count:,} parameters ({trainable_params:,} trainable)")

        # 2. Verify Optimizer Initialization
        print("[2/9] Verifying Optimizer Initialization...")
        learning_rate = 1e-3
        weight_decay = 0.1
        optimizer = configure_optimizers(model, weight_decay=weight_decay, learning_rate=learning_rate)
        assert optimizer is not None, "Optimizer initialization failed"
        assert len(optimizer.param_groups) == 2, "Optimizer expected 2 param groups (decay and no-decay)"
        print("  ✅ Optimizer initialized: AdamW with weight decay separation")

        # 3. Verify Scheduler Initialization
        print("[3/9] Verifying Scheduler Initialization...")
        warmup_steps = 2
        max_steps = 10
        scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps=warmup_steps, max_steps=max_steps)
        assert scheduler is not None, "Scheduler initialization failed"
        initial_lr = scheduler.get_last_lr()[0]
        print(f"  ✅ Scheduler initialized: Cosine Warmup, initial LR = {initial_lr}")

        # Synthetic batch (batch_size=2, seq_len=64)
        batch_size = 2
        seq_len = 64
        input_ids = torch.randint(0, model_config.vocab_size, (batch_size, seq_len))
        targets = torch.randint(0, model_config.vocab_size, (batch_size, seq_len))

        # 4. Run Exactly ONE Forward Pass
        print("[4/9] Executing Exactly ONE Forward Pass...")
        t0 = time.perf_counter()
        logits, loss = model(input_ids, targets=targets)
        t1 = time.perf_counter()
        forward_latency_ms = (t1 - t0) * 1000.0
        results["forward_latency_ms"] = forward_latency_ms
        assert logits is not None and loss is not None, "Forward pass returned None"
        assert not torch.isnan(loss), "Forward loss is NaN"
        print(f"  ✅ Forward pass completed: Loss = {loss.item():.4f}, Latency = {forward_latency_ms:.2f} ms")

        # 5. Run Exactly ONE Backward Pass
        print("[5/9] Executing Exactly ONE Backward Pass...")
        optimizer.zero_grad()
        t0 = time.perf_counter()
        loss.backward()
        t1 = time.perf_counter()
        backward_latency_ms = (t1 - t0) * 1000.0
        results["backward_latency_ms"] = backward_latency_ms

        has_grads = any(p.grad is not None and torch.abs(p.grad).sum() > 0 for p in model.parameters() if p.requires_grad)
        assert has_grads, "No non-zero gradients computed in backward pass"
        print(f"  ✅ Backward pass completed: Latency = {backward_latency_ms:.2f} ms")

        # 6. Run Exactly ONE Optimizer Step
        print("[6/9] Executing Exactly ONE Optimizer Step...")
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
        print("  ✅ Optimizer & Scheduler step completed")

        # 7. Verify Checkpoint Save
        print("[7/9] Verifying Checkpoint Save...")
        checkpoint_state = {
            "global_step": 1,
            "epoch": 0,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": loss.item(),
            "config": model_config
        }
        ckpt_path = save_checkpoint(checkpoint_state, test_dir, filename="quick_ckpt.ckpt")
        ckpt_file = Path(ckpt_path)
        json_file = ckpt_file.with_suffix(".json")

        assert ckpt_file.exists(), f"Checkpoint file {ckpt_file} not created"
        assert json_file.exists(), f"Sidecar JSON file {json_file} not created"
        ckpt_size_bytes = ckpt_file.stat().st_size
        ckpt_size_mb = ckpt_size_bytes / (1024 * 1024)
        results["checkpoint_size_mb"] = ckpt_size_mb
        print(f"  ✅ Checkpoint saved: {ckpt_file.name} ({ckpt_size_mb:.2f} MB)")

        # 8. Verify Checkpoint Load
        print("[8/9] Verifying Checkpoint Load...")
        fresh_model = NexaTransformer(model_config)
        fresh_optimizer = configure_optimizers(fresh_model, weight_decay=weight_decay, learning_rate=learning_rate)
        fresh_scheduler = get_cosine_schedule_with_warmup(fresh_optimizer, warmup_steps=warmup_steps, max_steps=max_steps)

        loaded_state = load_checkpoint(ckpt_file, fresh_model, fresh_optimizer, fresh_scheduler, device="cpu")
        assert loaded_state["global_step"] == 1, f"Expected global_step 1, got {loaded_state['global_step']}"

        for k, v in model.state_dict().items():
            assert k in fresh_model.state_dict(), f"Missing key {k} in loaded model state dict"
            assert torch.equal(v, fresh_model.state_dict()[k]), f"Mismatch in state dict tensor {k}"
        print("  ✅ Checkpoint loaded: Model parameters match saved state exactly")

        # 9. Verify Validation Executes on ONE Mini-Batch
        print("[9/9] Verifying Validation Execution on ONE Mini-Batch...")
        val_input_ids = torch.randint(0, model_config.vocab_size, (batch_size, seq_len))
        val_targets = torch.randint(0, model_config.vocab_size, (batch_size, seq_len))
        fresh_model.eval()
        with torch.no_grad():
            val_logits, val_loss = fresh_model(val_input_ids, val_targets)
        assert val_logits is not None and val_loss is not None, "Validation pass returned None"
        assert not torch.isnan(val_loss), "Validation loss is NaN"
        print(f"  ✅ Validation executed on 1 mini-batch: Val Loss = {val_loss.item():.4f}")

        # Peak RAM measurement (ru_maxrss in kB on Linux)
        max_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        max_rss_mb = max_rss_kb / 1024.0
        results["peak_ram_mb"] = max_rss_mb

        total_elapsed = time.time() - start_time

        print("\n====================================================")
        print("VERIFICATION METRICS SUMMARY")
        print("====================================================")
        print(f"• Parameter Count   : {results['parameter_count']:,} (~{results['parameter_count']/1e6:.1f}M)")
        print(f"• Forward Latency   : {results['forward_latency_ms']:.2f} ms")
        print(f"• Backward Latency  : {results['backward_latency_ms']:.2f} ms")
        print(f"• Checkpoint Size   : {results['checkpoint_size_mb']:.2f} MB")
        print(f"• Peak RAM Usage    : {results['peak_ram_mb']:.2f} MB")
        print(f"• Total Elapsed Time: {total_elapsed:.2f} s")
        print("====================================================")

        assert total_elapsed < 30.0, f"Verification exceeded 30s threshold ({total_elapsed:.2f}s)"
        print("🎉 ALL 10 ENGINEERING VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        print("====================================================")

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    run_quick_verification()
