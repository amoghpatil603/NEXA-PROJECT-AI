import json
from dataclasses import dataclass, field, asdict
import os
from pathlib import Path

def resolve_dataset_manifest() -> dict:
    candidates = [
        Path("data/manifest/final_manifest.json"),
        Path("backend/models/nexa_fm/data/manifest/final_manifest.json"),
        Path(__file__).resolve().parent.parent / "data/manifest/final_manifest.json",
        Path(__file__).resolve().parent.parent.parent.parent / "data/manifest/final_manifest.json"
    ]
    for c in candidates:
        if c.exists():
            with open(c, 'r', encoding='utf-8') as f:
                return json.load(f)
    raise FileNotFoundError("DATASET IDENTITY SOURCE NOT FOUND")

def get_tokenizer_sha256() -> str:
    candidates = [
        Path("backend/tokenizer_v1/tokenizer.json"),
        Path("tokenizer_v1/tokenizer.json"),
        Path(__file__).resolve().parent.parent.parent.parent / "backend/tokenizer_v1/tokenizer.json",
        Path(__file__).resolve().parent.parent.parent.parent / "tokenizer_v1/tokenizer.json"
    ]
    for c in candidates:
        if c.exists():
            import hashlib
            return hashlib.sha256(c.read_bytes()).hexdigest()
    raise FileNotFoundError("Authoritative tokenizer.json not found to establish identity!")

def get_tokenizer_config_sha256() -> str:
    candidates = [
        Path("backend/tokenizer_v1/tokenizer_config.json"),
        Path("tokenizer_v1/tokenizer_config.json"),
        Path(__file__).resolve().parent.parent.parent.parent / "backend/tokenizer_v1/tokenizer_config.json",
        Path(__file__).resolve().parent.parent.parent.parent / "tokenizer_v1/tokenizer_config.json"
    ]
    for c in candidates:
        if c.exists():
            import hashlib
            return hashlib.sha256(c.read_bytes()).hexdigest()
    raise FileNotFoundError("Authoritative tokenizer_config.json not found to establish configuration identity!")

@dataclass
class TrainingConfig:
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    warmup_steps: int = 1000
    max_steps: int = 100000
    save_steps: int = 1000
    log_steps: int = 10
    max_grad_norm: float = 1.0
    mixed_precision: bool = True
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
    dataset_dir: str = "data/shards"
    seed: int = 42
    dataset_version: str = ""
    dataset_content_hash: str = ""
    tokenizer_identity: str = ""
    tokenizer_config_identity: str = ""

    def __post_init__(self):
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be > 0")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be > 0")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be >= 0")
        if self.warmup_steps < 0:
            raise ValueError("warmup_steps must be >= 0")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be > 0")
        if self.save_steps <= 0:
            raise ValueError("save_steps must be > 0")
        if self.log_steps <= 0:
            raise ValueError("log_steps must be > 0")
        if self.max_grad_norm <= 0.0:
            raise ValueError("max_grad_norm must be > 0")
        if self.seed < 0:
            raise ValueError("seed must be >= 0")

        if not self.dataset_version or not self.dataset_content_hash:
            try:
                manifest = resolve_dataset_manifest()
                self.dataset_version = manifest.get("dataset_version", "")
                self.dataset_content_hash = manifest.get("content_hash", "")
            except Exception as e:
                raise ValueError(f"DATASET IDENTITY SOURCE NOT FOUND: {e}")
            if not self.dataset_version or not self.dataset_content_hash:
                raise ValueError("DATASET IDENTITY SOURCE NOT FOUND")

        if not self.tokenizer_identity:
            self.tokenizer_identity = get_tokenizer_sha256()
        if not self.tokenizer_config_identity:
            self.tokenizer_config_identity = get_tokenizer_config_sha256()

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
