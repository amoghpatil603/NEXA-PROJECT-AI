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

    Save semantics (FIX 2):
      1. Write all state into .tmp_checkpoint_<uuid>/
      2. Validate the temporary directory before touching the live path.
      3. Rename the previously-trusted final_path to .preserved_<uuid>/ (keeping it safe).
      4. Promote tmp -> final_path atomically.
      5. Remove the preserved copy ONLY after successful promotion and re-validation.
    If any step fails, the preserved copy is intact and a RuntimeError is raised.
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
        tmp_uid = uuid.uuid4().hex[:8]
        tmp_path = os.path.join(self.checkpoint_dir, f".tmp_checkpoint_{step}_{tmp_uid}")
        preserved_path = None
        os.makedirs(tmp_path, exist_ok=True)

        try:
            # --- Step 1: Capture all state ---
            rng_states = {
                'python_rng': random.getstate(),
                'numpy_rng': np.random.get_state(),
                'torch_cpu_rng': torch.get_rng_state() if torch else None,
                'torch_cuda_rng': torch.cuda.get_rng_state_all() if (torch and torch.cuda.is_available()) else None,
            }
            dataloader_state = {
                'current_shard_idx': getattr(dataloader, 'current_shard_idx', 0),
                'current_batch_idx': getattr(dataloader, 'current_batch_idx', 0)
            }
            scaler_state = scaler.state_dict() if scaler is not None else None

            # --- Step 1: Write state to temporary directory ---
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

            # --- Step 2: Validate temporary directory before touching live path ---
            if not self.is_checkpoint_valid(tmp_path):
                raise RuntimeError(
                    f"[CheckpointManager] Temporary checkpoint for step {step} failed validation "
                    f"before promotion. Training state is NOT lost — current in-memory state is intact. "
                    f"Aborting save to prevent corrupting trusted checkpoint directory."
                )

            # --- Step 3: Preserve the previous trusted checkpoint (do NOT delete yet) ---
            if os.path.exists(final_path):
                preserved_path = os.path.join(
                    self.checkpoint_dir, f".preserved_checkpoint_{step}_{tmp_uid}"
                )
                try:
                    os.rename(final_path, preserved_path)
                except Exception as e:
                    raise RuntimeError(
                        f"[CheckpointManager] Failed to move existing checkpoint-{step} "
                        f"to preservation path before promotion: {e}"
                    ) from e

            # --- Step 4: Promote tmp -> final_path atomically ---
            try:
                os.rename(tmp_path, final_path)
            except OSError:
                # Fallback for platforms where atomic directory rename fails (e.g. cross-device)
                if os.path.exists(final_path):
                    shutil.rmtree(final_path, ignore_errors=True)
                shutil.move(tmp_path, final_path)
            tmp_path = None  # Ownership transferred; do not clean up in finally

            # --- Step 5: Re-validate at final path, then remove preserved copy ---
            if not self.is_checkpoint_valid(final_path):
                # Promotion succeeded structurally but validation failed — restore from preserved
                if preserved_path and os.path.exists(preserved_path):
                    try:
                        if os.path.exists(final_path):
                            shutil.rmtree(final_path, ignore_errors=True)
                        os.rename(preserved_path, final_path)
                        preserved_path = None
                    except Exception:
                        pass
                raise RuntimeError(
                    f"[CheckpointManager] Post-promotion validation failed for checkpoint-{step}. "
                    f"Previous trusted checkpoint has been restored if available."
                )

            # Promotion and validation both succeeded — now safe to discard preserved copy
            if preserved_path and os.path.exists(preserved_path):
                shutil.rmtree(preserved_path, ignore_errors=True)
                preserved_path = None

        except Exception:
            # Ensure the preserved copy is never silently lost on any failure path
            if preserved_path and os.path.exists(preserved_path) and not os.path.exists(final_path):
                try:
                    os.rename(preserved_path, final_path)
                except Exception:
                    pass  # Best-effort: leave preserved copy on disk for manual recovery
            # Clean up an uncommitted tmp directory if it still exists
            if tmp_path and os.path.exists(tmp_path):
                shutil.rmtree(tmp_path, ignore_errors=True)
            raise

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

            if hasattr(dataloader, 'advance_cursor'):
                next_shard, next_batch = dataloader.advance_cursor(curr_shard, curr_batch)
                dataloader.start_shard_idx = next_shard
                dataloader.start_batch_idx = next_batch
            else:
                next_batch = curr_batch + getattr(dataloader, 'batch_size', 1)
                num_shards = len(getattr(dataloader, 'shards', []))
                if curr_shard < num_shards:
                    shard_path = dataloader.shards[curr_shard]
                    try:
                        data = np.memmap(shard_path, dtype=np.uint16, mode='r')
                        num_tokens = len(data)
                        num_sequences = num_tokens // getattr(dataloader, 'max_length', 2048)
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
