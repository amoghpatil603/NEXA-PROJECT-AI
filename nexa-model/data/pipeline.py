"""
Data Pipeline Module for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

Handles document ingestion, reading, and streaming processing.
"""

from pathlib import Path
from typing import Iterable, List, Union


def ingest_directory(dir_path: Union[str, Path], pattern: str = "*.txt") -> List[Path]:
    """
    Ingest text documents from a directory matching pattern deterministically sorted.
    """
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return []
    return sorted(list(p.glob(pattern)))


def process_documents(file_paths: List[Path]) -> Iterable[str]:
    """
    Generator yielding clean document strings from a list of file paths.
    """
    for path in file_paths:
        try:
            content = path.read_text(encoding="utf-8")
            if content:
                yield content
        except Exception as e:
            print(f"Warning: Failed to process document {path}: {e}")
