import hashlib
import json
from typing import List, Dict, Any
import random

def generate_content_hash(data_ids: List[Any], config: Dict[str, Any]) -> str:
    serialized_data = json.dumps(sorted(data_ids), sort_keys=True)
    serialized_config = json.dumps(config, sort_keys=True)
    combined = f"{serialized_data}|{serialized_config}"
    return hashlib.sha256(combined.encode()).hexdigest()

def deterministic_split(data_ids: List[Any], train_ratio: float = 0.9, seed: int = 42) -> Dict[str, List[Any]]:
    if not data_ids:
        return {'train': [], 'val': []}
    
    if isinstance(data_ids[0], dict) and 'source_id' in data_ids[0]:
        sorted_ids = sorted(data_ids, key=lambda x: x['source_id'])
    else:
        sorted_ids = sorted(data_ids)
        
    rng = random.Random(seed)
    rng.shuffle(sorted_ids)
    
    split_idx = int(len(sorted_ids) * train_ratio)
    return {'train': sorted_ids[:split_idx], 'val': sorted_ids[split_idx:]}

def generate_manifest(stats: Dict[str, Any]) -> str:
    content_hash = stats.get('content_hash', stats.get('hash', 'UNDEFINED'))
    dataset_version = f"1.0.0-{content_hash[:8]}" if content_hash != 'UNDEFINED' else "1.0.0"
    manifest = {
        "dataset_name": "NEXA",
        "dataset_version": dataset_version,
        "tokenizer_version": "nexa-bpe-v1",
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
        "split_seed": stats.get('seed', 42),
        "content_hash": content_hash
    }
    return json.dumps(manifest, indent=2)
