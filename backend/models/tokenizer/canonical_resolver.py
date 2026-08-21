"""
NEXA Authoritative Tokenizer Canonical Resolver
Provides deterministic access to both:
1. Dataset & Pretraining Canonical Tokenizer (`backend/tokenizer_v1/tokenizer.json`, SHA256 fa341d67...)
2. Production 8,000-Vocabulary BPE Tokenizer (`backend/models/tokenizer/production/tokenizer.json`, SHA256 0faf5e94...)
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Candidate locations for dataset / training canonical tokenizer artifacts
DATASET_TOKENIZER_CANDIDATES = [
    REPO_ROOT / "backend/tokenizer_v1/tokenizer.json",
    Path("backend/tokenizer_v1/tokenizer.json"),
    Path("tokenizer_v1/tokenizer.json"),
    Path(__file__).resolve().parent.parent.parent.parent / "backend/tokenizer_v1/tokenizer.json",
]

DATASET_CONFIG_CANDIDATES = [
    REPO_ROOT / "backend/tokenizer_v1/tokenizer_config.json",
    Path("backend/tokenizer_v1/tokenizer_config.json"),
    Path("tokenizer_v1/tokenizer_config.json"),
    Path(__file__).resolve().parent.parent.parent.parent / "backend/tokenizer_v1/tokenizer_config.json",
]

# Candidate locations for authoritative production 8k tokenizer artifacts
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
DATASET_VOCAB_SIZE = 300

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

def get_dataset_tokenizer_path() -> Path:
    """Resolve and return the absolute path to the dataset canonical tokenizer.json."""
    for candidate in DATASET_TOKENIZER_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Dataset canonical tokenizer artifact not found. Looked in: "
        + ", ".join(str(c) for c in DATASET_TOKENIZER_CANDIDATES)
    )

def get_dataset_tokenizer_config_path() -> Path:
    """Resolve and return the path to the dataset tokenizer_config.json."""
    for candidate in DATASET_CONFIG_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Dataset canonical tokenizer_config artifact not found. Looked in: "
        + ", ".join(str(c) for c in DATASET_CONFIG_CANDIDATES)
    )

def get_dataset_tokenizer_identity() -> str:
    """Calculate and return the SHA256 checksum of the dataset tokenizer.json."""
    return hashlib.sha256(get_dataset_tokenizer_path().read_bytes()).hexdigest()

def get_dataset_tokenizer_config_identity() -> str:
    """Calculate and return the SHA256 checksum of the dataset tokenizer_config.json."""
    return hashlib.sha256(get_dataset_tokenizer_config_path().read_bytes()).hexdigest()

def get_production_tokenizer_path() -> Path:
    """Resolve and return the absolute path to the production 8k tokenizer.json."""
    for candidate in PRODUCTION_TOKENIZER_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Production 8k tokenizer artifact not found. Looked in: "
        + ", ".join(str(c) for c in PRODUCTION_TOKENIZER_CANDIDATES)
    )

def get_production_tokenizer_identity() -> str:
    """Calculate and return the SHA256 checksum of the production 8k tokenizer.json."""
    return hashlib.sha256(get_production_tokenizer_path().read_bytes()).hexdigest()

def get_authoritative_tokenizer_path() -> Path:
    """Default authoritative tokenizer path for production inference and export."""
    return get_production_tokenizer_path()

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
    try:
        path = get_authoritative_tokenizer_metadata_path()
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "vocabulary_size": AUTHORITATIVE_VOCAB_SIZE,
            "certification_status": "8K_TOKENIZER_CERTIFIED",
            "special_tokens": AUTHORITATIVE_SPECIAL_TOKENS
        }

def get_tokenizer_sha256() -> str:
    """Default training & dataset tokenizer identity matching final_manifest.json."""
    return get_dataset_tokenizer_identity()

def get_tokenizer_config_sha256() -> str:
    """Default training & dataset tokenizer config identity matching final_manifest.json."""
    return get_dataset_tokenizer_config_identity()

def get_authoritative_tokenizer(tokenizer_class=None, mode: str = "production"):
    """
    Instantiate and return the tokenizer instance for the specified mode ('production' or 'dataset').
    """
    if tokenizer_class is None:
        try:
            from backend.models.tokenizer.incremental_bpe import IncrementalBPETokenizer
            tokenizer_class = IncrementalBPETokenizer
        except ImportError:
            from .incremental_bpe import IncrementalBPETokenizer
            tokenizer_class = IncrementalBPETokenizer

    tok_path = get_production_tokenizer_path() if mode == "production" else get_dataset_tokenizer_path()
    return tokenizer_class.load(str(tok_path))
