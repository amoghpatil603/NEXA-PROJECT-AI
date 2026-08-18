import os
try:
    import torch
except ImportError:
    torch = None
from .config import TrainingConfig
import json

import os
try:
    import torch
except ImportError:
    torch = None
from .config import TrainingConfig
import json
import random
import numpy as np

class CheckpointManager:
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save(self, model, optimizer, scheduler, step: int, micro_step: int, epoch: int, dataloader, config: TrainingConfig, scaler=None):
        if optimizer is None: return
        
        path = os.path.join(self.checkpoint_dir, f"checkpoint-{step}")
        os.makedirs(path, exist_ok=True)
        
        # Capture RNG states
        rng_states = {
            'python_rng': random.getstate(),
            'numpy_rng': np.random.get_state(),
            'torch_cpu_rng': torch.get_rng_state() if torch else None,
            'torch_cuda_rng': torch.cuda.get_rng_state_all() if (torch and torch.cuda.is_available()) else None,
        }
        
        # Capture dataloader cursor position
        dataloader_state = {
            'current_shard_idx': getattr(dataloader, 'current_shard_idx', 0),
            'current_batch_idx': getattr(dataloader, 'current_batch_idx', 0)
        }
        
        # Capture scaler state if exists
        scaler_state = scaler.state_dict() if scaler is not None else None
        
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'step': step,
            'micro_step': micro_step,
            'epoch': epoch,
            'rng_states': rng_states,
            'dataloader_state': dataloader_state,
            'scaler_state': scaler_state,
            'seed': config.seed
        }, os.path.join(path, "training_state.pt"))
        
        config.save(os.path.join(path, "training_config.json"))
        
    def load(self, path: str, model, optimizer=None, scheduler=None, dataloader=None, scaler=None):
        if not os.path.exists(path):
            return 0, 0, 0
            
        state_path = os.path.join(path, "training_state.pt")
        if not os.path.exists(state_path):
            return 0, 0, 0
            
        checkpoint = torch.load(state_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        if optimizer and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if scheduler and 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            
        # Restore RNG states
        if 'rng_states' in checkpoint:
            rng_states = checkpoint['rng_states']
            try:
                random.setstate(rng_states['python_rng'])
                np.random.set_state(rng_states['numpy_rng'])
                if torch and rng_states['torch_cpu_rng'] is not None:
                    torch.set_rng_state(rng_states['torch_cpu_rng'])
                if torch and rng_states['torch_cuda_rng'] is not None and torch.cuda.is_available():
                    torch.cuda.set_rng_state_all(rng_states['torch_cuda_rng'])
            except Exception as e:
                print(f"Warning: Failed to restore RNG states: {e}")
                    
        # Restore dataloader cursor position
        if dataloader and 'dataloader_state' in checkpoint:
            dataloader_state = checkpoint['dataloader_state']
            curr_shard = dataloader_state.get('current_shard_idx', 0)
            curr_batch = dataloader_state.get('current_batch_idx', 0)
            
            # We must resume from the NEXT batch index
            next_batch = curr_batch + dataloader.batch_size
            
            # Check length of sequences in the shard to see if we should advance to the next shard
            if curr_shard < len(dataloader.shards):
                shard_path = dataloader.shards[curr_shard]
                try:
                    data = np.memmap(shard_path, dtype=np.uint16, mode='r')
                    num_tokens = len(data)
                    num_sequences = num_tokens // dataloader.max_length
                    if next_batch >= num_sequences:
                        dataloader.start_shard_idx = curr_shard + 1
                        dataloader.start_batch_idx = 0
                    else:
                        dataloader.start_shard_idx = curr_shard
                        dataloader.start_batch_idx = next_batch
                except Exception:
                    dataloader.start_shard_idx = curr_shard
                    dataloader.start_batch_idx = next_batch
            else:
                dataloader.start_shard_idx = curr_shard
                dataloader.start_batch_idx = 0
                
            dataloader.current_shard_idx = dataloader.start_shard_idx
            dataloader.current_batch_idx = dataloader.start_batch_idx
            
        # Restore scaler state
        if scaler and checkpoint.get('scaler_state') is not None:
            try:
                scaler.load_state_dict(checkpoint['scaler_state'])
            except Exception as e:
                print(f"Warning: Failed to restore AMP GradScaler state: {e}")
            
        return checkpoint.get('step', 0), checkpoint.get('micro_step', 0), checkpoint.get('epoch', 0)
        
    def get_latest_checkpoint(self):
        if not os.path.exists(self.checkpoint_dir):
            return None
        checkpoints = [d for d in os.listdir(self.checkpoint_dir) if d.startswith("checkpoint-")]
        if not checkpoints:
            return None
        checkpoints.sort(key=lambda x: int(x.split("-")[1]))
        return os.path.join(self.checkpoint_dir, checkpoints[-1])
