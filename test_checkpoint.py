import torch
import os
import shutil
from model.config import NexaConfig
from model.transformer import NexaTransformer

def test_save_load():
    config = NexaConfig(vocab_size=100, max_seq_len=32, d_model=64, n_layers=2, n_heads=2, d_ff=128)
    model = NexaTransformer(config)
    
    # modify a weight
    with torch.no_grad():
        model.transformer.wte.weight[0, 0] = 999.0
        
    os.makedirs("checkpoints", exist_ok=True)
    
    # fake atomic save
    temp_path = "checkpoints/model.pt.tmp"
    final_path = "checkpoints/model.pt"
    torch.save(model.state_dict(), temp_path)
    os.replace(temp_path, final_path)
    
    # load
    model2 = NexaTransformer(config)
    model2.load_state_dict(torch.load(final_path))
    
    if model2.transformer.wte.weight[0, 0].item() != 999.0:
        raise ValueError("Load failed")
        
    print("Save/Load test PASS")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.absolute() / "nexa-model"))
    test_save_load()
