import sys
import torch
import torch.nn as nn

sys.path.insert(0, 'nexa-model')
from model.config import NexaConfig
from model.transformer import NexaTransformer
from training.optimizer import create_optimizer
from training.scheduler import get_cosine_schedule_with_warmup

def run_smoke_test():
    print("Initializing Nexa config and model...")
    config = NexaConfig(
        vocab_size=8000,
        max_seq_len=256,
        d_model=384,
        n_layers=6,
        n_heads=6,
        d_ff=1536,
        dropout=0.1,
        norm_eps=1e-5,
        weight_tying=True
    )
    model = NexaTransformer(config)
    
    print("Creating optimizer...")
    optimizer = create_optimizer(model, learning_rate=3e-4, weight_decay=0.1)
    
    print("Creating scheduler...")
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps=10, max_steps=100)
    
    print("Creating one test batch...")
    batch_size = 1
    seq_len = 256
    inputs = torch.randint(0, config.vocab_size, (batch_size, seq_len), dtype=torch.long)
    targets = torch.randint(0, config.vocab_size, (batch_size, seq_len), dtype=torch.long)
    
    print("Running forward pass...")
    model.train()
    logits, loss = model(inputs, targets)
    print(f"Forward pass successful! Loss: {loss.item():.4f}")
    
    print("Running backward pass...")
    loss.backward()
    print("Backward pass successful!")
    
    print("Running optimizer and scheduler step...")
    optimizer.step()
    if scheduler:
        scheduler.step()
    optimizer.zero_grad()
    print("Optimizer and scheduler step successful!")
    print("SMOKE TEST PASSED: NEXA_PHASE4E_READY")

if __name__ == "__main__":
    run_smoke_test()
