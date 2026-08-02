"""
Data Sharding Module for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

Provides efficient binary sharding and loading of token sequences.
"""

import json
import struct
from pathlib import Path
from typing import Iterable, List, Union


def create_shards(
    token_ids: Iterable[int],
    shard_size: int,
    output_dir: Path,
    prefix: str = "shard",
) -> List[Path]:
    """
    Pack token IDs into fixed-size binary shard files (using uint32).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shard_paths: List[Path] = []
    shard_idx = 0
    buffer: List[int] = []

    for tid in token_ids:
        buffer.append(tid)
        if len(buffer) >= shard_size:
            shard_file = output_dir / f"{prefix}_{shard_idx:05d}.bin"
            with open(shard_file, "wb") as f:
                f.write(struct.pack(f"<{len(buffer)}I", *buffer))
            shard_paths.append(shard_file)
            shard_idx += 1
            buffer = []

    if buffer:
        shard_file = output_dir / f"{prefix}_{shard_idx:05d}.bin"
        with open(shard_file, "wb") as f:
            f.write(struct.pack(f"<{len(buffer)}I", *buffer))
        shard_paths.append(shard_file)

    return shard_paths


def load_shard(shard_path: Path) -> List[int]:
    """
    Load token IDs from a binary shard file.
    """
    shard_path = Path(shard_path)
    if not shard_path.exists():
        raise FileNotFoundError(f"Shard file not found: {shard_path}")

    data = shard_path.read_bytes()
    num_tokens = len(data) // 4
    return list(struct.unpack(f"<{num_tokens}I", data))
