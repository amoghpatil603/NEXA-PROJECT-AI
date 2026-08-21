import unittest
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.models.tokenizer.canonical_resolver import (
    get_authoritative_tokenizer_path,
    get_authoritative_tokenizer_metadata,
    get_authoritative_tokenizer,
    get_dataset_tokenizer_path,
    get_dataset_tokenizer_identity,
    get_dataset_tokenizer_config_path,
    get_dataset_tokenizer_config_identity,
    get_production_tokenizer_path,
    get_production_tokenizer_identity,
    get_tokenizer_sha256,
    get_tokenizer_config_sha256,
    AUTHORITATIVE_VOCAB_SIZE,
    AUTHORITATIVE_SPECIAL_TOKENS
)
from backend.models.model.config import NexaConfig
from backend.models.nexa_fm.training_engine.config import TrainingConfig, resolve_dataset_manifest
from backend.models.tokenizer.bpe_tokenizer import NexaBPETokenizer
from backend.models.tokenizer.incremental_bpe import IncrementalBPETokenizer

class TestAuthoritativeTokenizer(unittest.TestCase):
    def test_authoritative_resolution(self):
        tok_path = get_authoritative_tokenizer_path()
        self.assertTrue(tok_path.exists(), f"Authoritative tokenizer file missing at {tok_path}")
        self.assertTrue(tok_path.is_file())

    def test_metadata_and_vocab_size(self):
        meta = get_authoritative_tokenizer_metadata()
        self.assertEqual(meta.get("vocabulary_size"), AUTHORITATIVE_VOCAB_SIZE)
        self.assertEqual(meta.get("vocabulary_size"), 8000)
        self.assertEqual(meta.get("certification_status"), "8K_TOKENIZER_CERTIFIED")

        # Verify model config matches
        cfg = NexaConfig.tiny()
        self.assertEqual(cfg.vocab_size, AUTHORITATIVE_VOCAB_SIZE)

    def test_special_tokens_consistency(self):
        meta = get_authoritative_tokenizer_metadata()
        meta_special = meta.get("special_tokens", {})
        for token, idx in AUTHORITATIVE_SPECIAL_TOKENS.items():
            self.assertIn(token, meta_special)
            self.assertEqual(meta_special[token], idx)

    def test_hashes_deterministic(self):
        h1 = get_tokenizer_sha256()
        h2 = get_tokenizer_sha256()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

        c1 = get_tokenizer_config_sha256()
        c2 = get_tokenizer_config_sha256()
        self.assertEqual(c1, c2)
        self.assertEqual(len(c1), 64)

    def test_manifest_tokenizer_identity_exact_reproduction(self):
        manifest = resolve_dataset_manifest()
        computed_tok_id = get_dataset_tokenizer_identity()
        computed_config_id = get_dataset_tokenizer_config_identity()

        self.assertEqual(
            computed_tok_id,
            manifest["tokenizer_identity"],
            f"Computed tokenizer identity {computed_tok_id} does not match manifest {manifest['tokenizer_identity']}"
        )
        self.assertEqual(
            computed_config_id,
            manifest["metadata"]["dataset_config"]["tokenizer_config_identity"],
            f"Computed tokenizer config identity {computed_config_id} does not match manifest"
        )

    def test_training_config_and_manifest_identity_harmony(self):
        manifest = resolve_dataset_manifest()
        config = TrainingConfig()

        self.assertEqual(config.tokenizer_identity, manifest["tokenizer_identity"])
        self.assertEqual(
            config.tokenizer_config_identity,
            manifest["metadata"]["dataset_config"]["tokenizer_config_identity"]
        )

    def test_special_tokens_shared_between_dataset_and_production(self):
        # Both dataset and production tokenizers must share the identical 12 special token IDs (0..11)
        dataset_cfg_path = get_dataset_tokenizer_config_path()
        with open(dataset_cfg_path, "r", encoding="utf-8") as f:
            dataset_cfg = json.load(f)

        dataset_specials = dataset_cfg.get("special_tokens", {})
        for token, idx in AUTHORITATIVE_SPECIAL_TOKENS.items():
            self.assertIn(token, dataset_specials)
            self.assertEqual(dataset_specials[token], idx)

    def test_incremental_and_bpe_loading(self):
        tok_inc = get_authoritative_tokenizer(IncrementalBPETokenizer, mode="production")
        tok_bpe = get_authoritative_tokenizer(NexaBPETokenizer, mode="production")

        sample_text = "The NEXA neural architecture delivers local AI reasoning with deep efficiency."
        encoded_inc = tok_inc.encode(sample_text)
        encoded_bpe = tok_bpe.encode(sample_text)

        self.assertEqual(encoded_inc, encoded_bpe)
        self.assertTrue(all(0 <= token_id < AUTHORITATIVE_VOCAB_SIZE for token_id in encoded_inc))

        decoded_inc = tok_inc.decode(encoded_inc)
        self.assertEqual(decoded_inc, sample_text)

if __name__ == "__main__":
    unittest.main()
