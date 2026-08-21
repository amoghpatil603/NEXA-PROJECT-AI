"""
NEXA Authoritative Tokenizer Canonical Resolver
Provides deterministic access to the certified 8,000-vocabulary BPE tokenizer and metadata.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Candidate locations for authoritative production tokenizer artifacts
PRODUCTION_TOKENIZER_CANDIDATES = [
    REPO_ROOT / "backend/models/tokenizer/production/tokenizer.json",
    Path("backend/models/tokenizer/production/tokenizer.json"),
    Path(__file__).resolve().parent / "production/tokenizer.json",
    Path("models/tokenizer/production/tokenizer.json"),
]

PRODUCTION_METADATA_CANDIDATES = [
    REPO_ROOT / "backend/models/tokenizer/production/metadata.json",
    Path("backend/models/tokenizer/production/metadata.json"),
    Path(__file__).resolve().parent / "production/metadata.json",
    Path("models/tokenizer/production/metadata.json"),
]

AUTHORITATIVE_VOCAB_SIZE = 8000

AUTHORITATIVE_SPECIAL_TOKENS = {
    "<PAD>": 0,
    "<BOS>": 1,
    "<EOS>": 2,
    "<UNK>": 3,
    "<NEXA_PAD>": 4,
    "<NEXA_BOS>": 5,
    "<NEXA_EOS>": 6,
    "<NEXA_UNK>": 7,
    "<NEXA_SYSTEM>": 8,
    "<NEXA_USER>": 9,
    "<NEXA_ASSISTANT>": 10,
    "<NEXA_END>": 11,
}

def get_authoritative_tokenizer_path() -> Path:
    """Resolve and return the absolute path to the authoritative production tokenizer.json."""
    for candidate in PRODUCTION_TOKENIZER_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Authoritative production tokenizer artifact not found. Looked in: "
        + ", ".join(str(c) for c in PRODUCTION_TOKENIZER_CANDIDATES)
    )

def get_authoritative_tokenizer_metadata_path() -> Path:
    """Resolve and return the path to the production metadata.json."""
    for candidate in PRODUCTION_METADATA_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Authoritative production tokenizer metadata not found. Looked in: "
        + ", ".join(str(c) for c in PRODUCTION_METADATA_CANDIDATES)
    )

def get_authoritative_tokenizer_metadata() -> Dict[str, Any]:
    """Load and return the production tokenizer metadata dictionary."""
    path = get_authoritative_tokenizer_metadata_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_tokenizer_sha256() -> str:
    """Calculate and return the SHA256 checksum of the authoritative tokenizer artifact."""
    path = get_authoritative_tokenizer_path()
    return hashlib.sha256(path.read_bytes()).hexdigest()

def get_tokenizer_config_sha256() -> str:
    """Calculate and return the SHA256 checksum of the authoritative tokenizer metadata/config."""
    path = get_authoritative_tokenizer_metadata_path()
    return hashlib.sha256(path.read_bytes()).hexdigest()

def get_authoritative_tokenizer(tokenizer_class=None):
    """
    Instantiate and return the authoritative tokenizer instance.
    Defaults to IncrementalBPETokenizer if not specified.
    """
    if tokenizer_class is None:
        try:
            from backend.models.tokenizer.incremental_bpe import IncrementalBPETokenizer
            tokenizer_class = IncrementalBPETokenizer
        except ImportError:
            from .incremental_bpe import IncrementalBPETokenizer
            tokenizer_class = IncrementalBPETokenizer

    tok_path = get_authoritative_tokenizer_path()
    return tokenizer_class.load(str(tok_path))
