import os
import torch
import numpy as np
from pathlib import Path
from typing import Iterator, List, Optional

class ShardDataLoader:
    """
    Production DataLoader: Reads uint16 binary shards using memory-mapping.
    Produces (batch_size, sequence_length) torch.long tensors.
    Supports local paths, external directories (Drive / mount), nested splits (train/val/test),
    and exact restart-safe cursor tracking.
    """
    def __init__(
        self,
        shard_dir: str | Path,
        batch_size: int = 1,
        max_length: int = 2048,
        shuffle: bool = True,
        seed: int = 42,
        start_shard_idx: int = 0,
        start_batch_idx: int = 0,
        drop_last: bool = False
    ):
        self.shard_dir = Path(shard_dir).resolve() if isinstance(shard_dir, (str, Path)) else Path(shard_dir)
        if not self.shard_dir.exists():
            raise FileNotFoundError(f"Dataset directory does not exist: '{self.shard_dir}'")

        self.batch_size = batch_size
        self.max_length = max_length
        self.shuffle = shuffle
        self.seed = seed
        self.start_shard_idx = start_shard_idx
        self.start_batch_idx = start_batch_idx
        self.drop_last = drop_last
        self.current_shard_idx = start_shard_idx
        self.current_batch_idx = start_batch_idx

        # Discover shards: check train/ subfolder first if present, then flat, then recursive
        train_subdir = self.shard_dir / "train"
        if train_subdir.exists() and train_subdir.is_dir():
            discovered = sorted(list(train_subdir.glob("*.bin")))
        else:
            discovered = sorted(list(self.shard_dir.glob("*.bin")))
            if not discovered:
                discovered = sorted(list(self.shard_dir.glob("**/*.bin")))

        if not discovered:
            raise FileNotFoundError(
                f"No binary shards (*.bin) found in dataset directory '{self.shard_dir}' or its subdirectories."
            )

        self.shards: List[Path] = discovered

        # Validate that discovered shards are readable and non-empty
        for shard_file in self.shards:
            if not shard_file.is_file():
                raise FileNotFoundError(f"Expected shard file at '{shard_file}', but it is not a valid file.")
            if os.path.getsize(shard_file) == 0:
                raise ValueError(f"Found empty binary shard file (0 bytes): '{shard_file}'")

    def _get_shuffled_indices(self) -> np.ndarray:
        indices = np.arange(len(self.shards))
        if self.shuffle:
            rng = np.random.default_rng(self.seed)
            rng.shuffle(indices)
        return indices

    def get_shard_path(self, s_idx: int) -> Path:
        """Return the shard Path corresponding to sequence index s_idx."""
        indices = self._get_shuffled_indices()
        if s_idx < 0 or s_idx >= len(indices):
            raise IndexError(f"Shard index {s_idx} out of range [0, {len(indices)}).")
        return self.shards[indices[s_idx]]

    def get_num_sequences_in_shard(self, s_idx: int) -> int:
        """Calculate the total number of complete/padded sequences in shard s_idx without loading into RAM."""
        shard_path = self.get_shard_path(s_idx)
        file_bytes = os.path.getsize(shard_path)
        num_tokens = file_bytes // 2  # uint16 is 2 bytes per token
        num_sequences = num_tokens // self.max_length
        if num_sequences == 0 and num_tokens > 0:
            return 1
        return num_sequences

    def advance_cursor(self, curr_shard: int, curr_batch: int) -> tuple[int, int]:
        """
        Calculate next (shard_idx, batch_idx) after executing a step with batch_size.
        Handles shard boundary wrap-around cleanly.
        """
        next_batch = curr_batch + self.batch_size
        num_shards = len(self.shards)
        if curr_shard < num_shards:
            num_seqs = self.get_num_sequences_in_shard(curr_shard)
            if next_batch >= num_seqs:
                # Advance to next shard
                return curr_shard + 1, 0
            else:
                return curr_shard, next_batch
        return curr_shard, 0

    def __iter__(self) -> Iterator[torch.Tensor]:
        indices = self._get_shuffled_indices()

        for s_idx in range(self.start_shard_idx, len(indices)):
            idx = indices[s_idx]
            shard_path = self.shards[idx]
            # Zero-copy memory mapping
            data = np.memmap(shard_path, dtype=np.uint16, mode='r')
            num_tokens = len(data)
            num_sequences = num_tokens // self.max_length
            if num_sequences == 0:
                if num_tokens > 0:
                    padded = np.zeros(self.max_length, dtype=np.uint16)
                    padded[:num_tokens] = data[:]
                    sequences = padded.reshape(1, self.max_length)
                else:
                    continue
            else:
                sequences = data[:num_sequences * self.max_length].reshape(-1, self.max_length)

            start_b = self.start_batch_idx if s_idx == self.start_shard_idx else 0

            for i in range(start_b, len(sequences), self.batch_size):
                batch = sequences[i:i + self.batch_size]
                if self.drop_last and len(batch) < self.batch_size:
                    continue
                if len(batch) == 0:
                    continue
                self.current_shard_idx = s_idx
                self.current_batch_idx = i
                # Cast to int64 for embeddings input mapping in PyTorch
                yield torch.from_numpy(batch.astype(np.int64))

            # Reset start_batch_idx for subsequent shards
            self.start_batch_idx = 0

        # Reset start_shard_idx for subsequent iterations/epochs
        self.start_shard_idx = 0