import os
import re
import uuid
import shutil
try:
    import torch
except ImportError:
    torch = None
from .config import TrainingConfig
import json
import random
import numpy as np

class CheckpointManager:
    """
    Manages atomic checkpoint saving, robust latest checkpoint discovery,
    and exact state restoration with identity integrity guards.
    """
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self._cleanup_stale_temp_dirs()

    def _cleanup_stale_temp_dirs(self):
        """Remove any abandoned temporary checkpoint directories from past interrupted runs."""
        if not os.path.exists(self.checkpoint_dir):
            return
        for item in os.listdir(self.checkpoint_dir):
            if item.startswith(".tmp_checkpoint_"):
                tmp_path = os.path.join(self.checkpoint_dir, item)
                try:
                    if os.path.isdir(tmp_path):
                        shutil.rmtree(tmp_path, ignore_errors=True)
                    else:
                        os.remove(tmp_path)
                except Exception:
                    pass

    def save(self, model, optimizer, scheduler, step: int, micro_step: int, epoch: int, dataloader, config: TrainingConfig, scaler=None):
        if optimizer is None or torch is None:
            return

        final_path = os.path.join(self.checkpoint_dir, f"checkpoint-{step}")
        tmp_path = os.path.join(self.checkpoint_dir, f".tmp_checkpoint_{step}_{uuid.uuid4().hex[:8]}")
        os.makedirs(tmp_path, exist_ok=True)

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

        # Write state to temporary directory
        state_file = os.path.join(tmp_path, "training_state.pt")
        config_file = os.path.join(tmp_path, "training_config.json")

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
            'seed': config.seed,
            'dataset_version': config.dataset_version,
            'dataset_content_hash': config.dataset_content_hash,
            'tokenizer_identity': config.tokenizer_identity,
            'tokenizer_config_identity': config.tokenizer_config_identity
        }, state_file)

        config.save(config_file)

        # Atomic promotion to final path
        if os.path.exists(final_path):
            backup_path = os.path.join(self.checkpoint_dir, f".old_checkpoint_{step}_{uuid.uuid4().hex[:8]}")
            try:
                os.rename(final_path, backup_path)
                shutil.rmtree(backup_path, ignore_errors=True)
            except Exception:
                shutil.rmtree(final_path, ignore_errors=True)

        try:
            os.rename(tmp_path, final_path)
        except OSError:
            # Fallback on platforms where atomic directory rename over existing fails
            if os.path.exists(final_path):
                shutil.rmtree(final_path, ignore_errors=True)
            shutil.move(tmp_path, final_path)

    def is_checkpoint_valid(self, path: str) -> bool:
        """Verify that a checkpoint directory is structurally complete and readable."""
        if not os.path.isdir(path):
            return False

        state_path = os.path.join(path, "training_state.pt")
        config_path = os.path.join(path, "training_config.json")

        if not os.path.isfile(state_path) or not os.path.isfile(config_path):
            return False

        # File size check (must not be zero bytes or empty stub)
        if os.path.getsize(state_path) < 128 or os.path.getsize(config_path) == 0:
            return False

        # Quick structural load check
        if torch is not None:
            try:
                ckpt = torch.load(state_path, map_location="cpu", weights_only=False)
                if not isinstance(ckpt, dict) or 'model_state_dict' not in ckpt:
                    return False
            except Exception:
                return False

        return True

    def get_latest_checkpoint(self):
        """
        Discovers the latest valid checkpoint, sorted numerically by step.
        Incomplete temporary directories or corrupted checkpoints are automatically skipped.
        """
        if not os.path.exists(self.checkpoint_dir):
            return None

        candidates = []
        for entry in os.listdir(self.checkpoint_dir):
            if entry.startswith(".") or entry.startswith("tmp"):
                continue
            match = re.match(r"^checkpoint-(\d+)$", entry)
            if match:
                step_val = int(match.group(1))
                candidates.append((step_val, entry))

        if not candidates:
            return None

        # Sort descending by step number
        candidates.sort(key=lambda x: x[0], reverse=True)

        for step_val, entry in candidates:
            full_path = os.path.join(self.checkpoint_dir, entry)
            if self.is_checkpoint_valid(full_path):
                return full_path
            else:
                print(f"Warning: Checkpoint at '{full_path}' is corrupted or incomplete; skipping to previous valid checkpoint.")

        return None

    def load(self, path: str, model, optimizer=None, scheduler=None, dataloader=None, scaler=None, config: TrainingConfig = None):
        if not os.path.exists(path):
            return 0, 0, 0

        state_path = os.path.join(path, "training_state.pt")
        if not os.path.exists(state_path):
            return 0, 0, 0

        checkpoint = torch.load(state_path, map_location="cpu", weights_only=False)

        # Enforce compatibility guards
        if not isinstance(checkpoint, dict) or 'model_state_dict' not in checkpoint:
            raise ValueError("Malformed checkpoint: missing 'model_state_dict'")

        required_metadata = ['dataset_version', 'dataset_content_hash', 'tokenizer_identity', 'tokenizer_config_identity']
        for key in required_metadata:
            if key not in checkpoint or checkpoint[key] is None or checkpoint[key] == "":
                raise ValueError(f"Malformed checkpoint: missing or empty metadata key '{key}'")

        if config is not None:
            if checkpoint.get('dataset_version') != config.dataset_version:
                raise ValueError(f"Dataset version mismatch: checkpoint has '{checkpoint.get('dataset_version')}', config has '{config.dataset_version}'")
            if checkpoint.get('dataset_content_hash') != config.dataset_content_hash:
                raise ValueError(f"Dataset content hash mismatch: checkpoint has '{checkpoint.get('dataset_content_hash')}', config has '{config.dataset_content_hash}'")
            if checkpoint.get('tokenizer_identity') != config.tokenizer_identity:
                raise ValueError(f"Tokenizer identity mismatch: checkpoint has '{checkpoint.get('tokenizer_identity')}', config has '{config.tokenizer_identity}'")
            if checkpoint.get('tokenizer_config_identity') != config.tokenizer_config_identity:
                raise ValueError(f"Tokenizer config identity mismatch: checkpoint has '{checkpoint.get('tokenizer_config_identity')}', config has '{config.tokenizer_config_identity}'")

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
