import hashlib
import json
from typing import List, Dict, Any

def generate_content_hash(data_ids: List[Any], config: Dict[str, Any]) -> str:
    """Generates a deterministic hash representing the dataset state and config."""
    serialized_data = json.dumps(sorted([str(idx) for idx in data_ids]), sort_keys=True)
    serialized_config = json.dumps(config, sort_keys=True)
    combined = f"{serialized_data}|{serialized_config}"
    return hashlib.sha256(combined.encode()).hexdigest()

def deterministic_split(input_docs: List[Any], train_ratio: float = 0.8, validation_ratio: float = 0.1, seed: int = 42) -> Dict[str, List[Any]]:
    """Splits data into train/validation/test sets deterministically by sorting on a stable key or value."""
    if not input_docs:
        return {'train': [], 'validation': [], 'test': []}
        
    def get_id(x):
        if isinstance(x, dict):
            return str(x.get('source_id', x.get('id', '')))
        return str(x)

    sorted_docs = sorted(input_docs, key=get_id)
    import random
    rng = random.Random(seed)
    rng.shuffle(sorted_docs)

    n = len(sorted_docs)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + validation_ratio))
    
    return {
        'train': sorted_docs[:train_end],
        'validation': sorted_docs[train_end:val_end],
        'test': sorted_docs[val_end:]
    }

def generate_manifest(stats: Dict[str, Any], data_ids: List[Any] = None, dataset_config: Dict[str, Any] = None) -> str:
    """
    Generates a manifest. If data_ids and dataset_config are provided,
    derives the content_hash and dataset_version deterministically.
    """
    content_hash = stats.get('hash', stats.get('content_hash', 'UNDEFINED'))

    if data_ids is not None and dataset_config is not None:
        content_hash = generate_content_hash(data_ids, dataset_config)

    # Certification requirement: version must be '1.0.0-{prefix}'
    dataset_version = f"1.0.0-{content_hash[:8]}" if content_hash != 'UNDEFINED' else "1.0.0-PROTOTYPE"

    manifest = {
        "dataset_name": stats.get('dataset_name', 'NEXA'),
        "dataset_version": dataset_version,
        "tokenizer_version": stats.get('tokenizer_version', 'nexa-bpe-v1'),
        "vocab_size": stats.get('vocab_size', 0),
        "train_documents": stats.get('train_documents', 0),
        "validation_documents": stats.get('validation_documents', 0),
        "test_documents": stats.get('test_documents', 0),
        "train_tokens": stats.get('train_tokens', 0),
        "validation_tokens": stats.get('validation_tokens', 0),
        "test_tokens": stats.get('test_tokens', 0),
        "shard_format": "uint16_binary",
        "shard_count": stats.get('shard_count', 0),
        "sequence_length": stats.get('max_length', 2048),
        "split_seed": stats.get('seed', stats.get('split_seed', 42)),
        "content_hash": content_hash,
        "metadata": {
            "seed": stats.get('seed', stats.get('split_seed', 42)),
            "content_hash": content_hash
        }
    }
    return json.dumps(manifest, indent=2)
