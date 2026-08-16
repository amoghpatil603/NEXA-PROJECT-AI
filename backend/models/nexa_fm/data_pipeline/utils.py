import hashlib
import json
from typing import List, Dict, Any

def generate_content_hash(data_ids: List[Any], config: Dict[str, Any]) -> str:
    """Generates a deterministic hash representing the dataset state and config."""
    serialized_data = json.dumps(sorted(data_ids), sort_keys=True)
    serialized_config = json.dumps(config, sort_keys=True)
    combined = f"{serialized_data}|{serialized_config}"
    return hashlib.sha256(combined.encode()).hexdigest()

def deterministic_split(data_ids: List[Any], train_ratio: float = 0.9, seed: int = 42) -> Dict[str, List[Any]]:
    sorted_ids = sorted(data_ids)
    import random
    rng = random.Random(seed)
    rng.shuffle(sorted_ids)
    split_idx = int(len(sorted_ids) * train_ratio)
    return {'train': sorted_ids[:split_idx], 'val': sorted_ids[split_idx:]}

def generate_manifest(stats: Dict[str, Any]) -> str:
    manifest = {
        "dataset_name": "NEXA",
        "dataset_version": "1.0.0",
        "tokenizer_version": "nexa-bpe-v1",
        "vocab_size": stats.get('vocab_size', 0),
        "train_documents": stats.get('train_documents', 0), # Added missing field
        "validation_documents": stats.get('val_documents', 0), # Added missing field
        "train_tokens": stats.get('train_tokens', 0),
        "validation_tokens": stats.get('val_tokens', 0),
        "shard_format": "uint16_binary",
        "content_hash": stats.get('content_hash', 'UNDEFINED')
    }
    return json.dumps(manifest, indent=2)
