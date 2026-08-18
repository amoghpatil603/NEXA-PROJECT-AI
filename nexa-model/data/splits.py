"""
Data Splitting Module for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

Provides deterministic train/val/test document splitting with small-corpus protection
to prevent empty validation or test splits due to percentage rounding.
"""

import random
from pathlib import Path
from typing import Dict, List, Tuple, Union


def split_documents(
    doc_paths: List[Path],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> Dict[str, List[Path]]:
    """
    Split document paths into train, val, and test sets deterministically.

    Small-corpus protection:
    - If total documents >= 3, guarantees at least 1 document in val and 1 in test.
    - If total documents == 2, guarantees at least 1 in train and 1 in val.
    - If total documents == 1, assigns to train.
    """
    if not doc_paths:
        return {"train": [], "val": [], "test": []}

    # Deterministic shuffle
    paths = sorted(list(doc_paths))
    rng = random.Random(seed)
    rng.shuffle(paths)

    total = len(paths)

    if total >= 3:
        n_val = max(1, int(round(total * val_ratio)))
        n_test = max(1, int(round(total * test_ratio)))
        # Ensure train gets remaining
        if n_val + n_test >= total:
            n_val = 1
            n_test = 1
        n_train = total - n_val - n_test

        train_paths = paths[:n_train]
        val_paths = paths[n_train : n_train + n_val]
        test_paths = paths[n_train + n_val :]
    elif total == 2:
        train_paths = [paths[0]]
        val_paths = [paths[1]]
        test_paths = []
    else:  # total == 1
        train_paths = [paths[0]]
        val_paths = []
        test_paths = []

    return {
        "train": train_paths,
        "val": val_paths,
        "test": test_paths,
    }
