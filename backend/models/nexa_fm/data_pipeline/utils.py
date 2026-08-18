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

def generate_manifest(stats: Dict[str, Any], data_ids: List[Any], dataset_config: Dict[str, Any]) -> str:
    """
    Generates a manifest. Enforces that both data_ids and dataset_config are provided
    and contain all authoritative configuration keys.
    """
    if data_ids is None or dataset_config is None:
        raise ValueError("Both data_ids and dataset_config are strictly required for manifest generation.")

    required_keys = [
        "train_ratio",
        "validation_ratio",
        "test_ratio",
        "split_seed",
        "shard_size",
        "sequence_length",
        "tokenizer_identity",
        "tokenizer_config_identity",
        "cleaning_version"
    ]
    for key in required_keys:
        if key not in dataset_config or dataset_config[key] is None or dataset_config[key] == "":
            raise ValueError(f"Missing required configuration key: {key}")

    content_hash = generate_content_hash(data_ids, dataset_config)
    dataset_version = f"1.0.0-{content_hash[:8]}"

    config_identity = hashlib.sha256(json.dumps(dataset_config, sort_keys=True).encode()).hexdigest()

    manifest = {
        "dataset_name": stats.get('dataset_name', 'NEXA'),
        "dataset_version": dataset_version,
        "tokenizer_version": dataset_config["tokenizer_identity"],
        "tokenizer_identity": dataset_config["tokenizer_identity"],
        "vocab_size": stats.get('vocab_size', 0),
        "train_documents": stats.get('train_documents', 0),
        "validation_documents": stats.get('validation_documents', 0),
        "test_documents": stats.get('test_documents', 0),
        "train_tokens": stats.get('train_tokens', 0),
        "validation_tokens": stats.get('validation_tokens', 0),
        "test_tokens": stats.get('test_tokens', 0),
        "shard_format": "uint16_binary",
        "shard_count": stats.get('shard_count', 0),
        "sequence_length": dataset_config["sequence_length"],
        "split_seed": dataset_config["split_seed"],
        "content_hash": content_hash,
        "shard_checksums": stats.get("shard_checksums", {}),
        "dataset_config_identity": config_identity,
        "metadata": {
            "seed": dataset_config["split_seed"],
            "content_hash": content_hash,
            "dataset_config": dataset_config,
            "dataset_config_identity": config_identity
        }
    }
    return json.dumps(manifest, indent=2)
