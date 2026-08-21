"""
Tokenizer Training Entry Point for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

This module provides CLI and programmatic entry points for training NexaBPETokenizer
or IncrementalBPETokenizer on specified text corpora.

MUST NOT start training automatically upon import.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS
    from tokenizer.incremental_bpe import IncrementalBPETokenizer
except ImportError:
    try:
        from .bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS
        from .incremental_bpe import IncrementalBPETokenizer
    except ImportError:
        from backend.models.tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS
        from backend.models.tokenizer.incremental_bpe import IncrementalBPETokenizer


def load_corpus_documents(corpus_path: Path) -> List[str]:
    """Load documents from a file or directory of .txt files."""
    docs: List[str] = []
    if corpus_path.is_file():
        docs.append(corpus_path.read_text(encoding="utf-8"))
    elif corpus_path.is_dir():
        for f in sorted(corpus_path.glob("*.txt")):
            try:
                text = f.read_text(encoding="utf-8")
                if text.strip():
                    docs.append(text)
            except Exception as e:
                print(f"Warning: Failed to read {f}: {e}")
    else:
        raise FileNotFoundError(f"Corpus path not found: {corpus_path}")
    return docs


def train_tokenizer(
    corpus_path: Path,
    output_dir: Path,
    vocab_size: int = 8000,
    min_frequency: int = 2,
    algorithm: str = "incremental",
) -> Path:
    """
    Train a NEXA BPE tokenizer on the specified corpus.
    """
    docs = load_corpus_documents(corpus_path)
    print(f"Loaded {len(docs)} documents from {corpus_path}")

    if algorithm == "incremental":
        tok = IncrementalBPETokenizer(
            vocab_size=vocab_size,
            min_frequency=min_frequency,
            special_tokens=DEFAULT_SPECIAL_TOKENS,
        )
    elif algorithm == "reference":
        tok = NexaBPETokenizer(
            vocab_size=vocab_size,
            min_frequency=min_frequency,
            special_tokens=DEFAULT_SPECIAL_TOKENS,
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Choose 'incremental' or 'reference'.")

    print(f"Training {algorithm} tokenizer (target vocab_size={vocab_size}, min_freq={min_frequency})...")
    tok.train(docs)

    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "tokenizer.json"
    tok.save(save_path)
    print(f"Tokenizer saved successfully to {save_path} (final vocab count: {len(tok.vocab) + len(tok.special_tokens)})")
    return save_path


def main():
    parser = argparse.ArgumentParser(description="NEXA Tokenizer Trainer")
    parser.add_argument("--corpus", type=str, required=True, help="Path to text file or directory")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save tokenizer.json")
    parser.add_argument("--vocab-size", type=int, default=8000, help="Target vocabulary size")
    parser.add_argument("--min-frequency", type=int, default=2, help="Minimum pair frequency")
    parser.add_argument("--algorithm", type=str, choices=["incremental", "reference"], default="incremental")

    args = parser.parse_args()
    train_tokenizer(
        corpus_path=Path(args.corpus),
        output_dir=Path(args.output_dir),
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        algorithm=args.algorithm,
    )


if __name__ == "__main__":
    main()
