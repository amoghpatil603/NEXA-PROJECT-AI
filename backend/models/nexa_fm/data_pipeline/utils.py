
import hashlib
import json
from typing import List, Dict, Any

def deterministic_split(data_ids: List[Any], train_ratio: float = 0.9, seed: int = 42) -> Dict[str, List[Any]]:
    sorted_ids = sorted(data_ids)
    import random
    rng = random.Random(seed)
    rng.shuffle(sorted_ids)
    split_idx = int(len(sorted_ids) * train_ratio)
    return {
        'train': sorted_ids[:split_idx],
        'val': sorted_ids[split_idx:]
    }

def generate_manifest(stats: Dict[str, Any]) -> str:
    manifest = {
        "dataset_name": "NEXA",
        "dataset_version": "1.0.0",
        "tokenizer_version": "nexa-bpe-v1",
        "vocab_size": stats.get('vocab_size', 0),
        "train_tokens": stats.get('train_tokens', 0),
        "validation_tokens": stats.get('val_tokens', 0),
        "shard_format": "uint16_binary",
        "shard_count": stats.get('shard_count', 0),
        "sequence_length": stats.get('max_length', 2048),
        "split_seed": stats.get('seed', 42),
        "content_hash": stats.get('hash', '0')
    }
    return json.dumps(manifest, indent=2)
