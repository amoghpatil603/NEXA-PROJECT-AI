import unittest
import json
import hashlib
from typing import Dict, Any
from backend.models.nexa_fm.data_pipeline.utils import generate_content_hash, generate_manifest

class TestDatasetIdentityHashing(unittest.TestCase):
    def setUp(self):
        self.data_ids = ["doc_a", "doc_b", "doc_c"]
        self.base_config = {
            "train_ratio": 0.8,
            "validation_ratio": 0.1,
            "test_ratio": 0.1,
            "split_seed": 42,
            "shard_size": 50000,
            "sequence_length": 2048,
            "tokenizer_identity": "267870a26a483f86b2543acfc863773fabb13d802c8085baad475487ab0f11c8",
            "tokenizer_config_identity": "987654321abcdef",
            "cleaning_version": "gutenberg_cleaning_v1"
        }
        self.stats = {
            "vocab_size": 300,
            "train_documents": 2,
            "validation_documents": 1,
            "test_documents": 0,
            "train_tokens": 1000,
            "validation_tokens": 500,
            "test_tokens": 0,
            "shard_count": 2,
            "shard_checksums": {
                "train/shard_00000.bin": {"sha256": "fake_sha_a"},
                "validation/shard_00000.bin": {"sha256": "fake_sha_b"}
            }
        }

    def test_hash_sensitivity(self):
        base_hash = generate_content_hash(self.data_ids, self.base_config)

        # 1. Test train_ratio sensitivity
        config_train = self.base_config.copy()
        config_train["train_ratio"] = 0.7
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_train))

        # 2. Test validation_ratio sensitivity
        config_val = self.base_config.copy()
        config_val["validation_ratio"] = 0.15
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_val))

        # 3. Test test_ratio sensitivity
        config_test = self.base_config.copy()
        config_test["test_ratio"] = 0.15
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_test))

        # 4. Test split_seed sensitivity
        config_seed = self.base_config.copy()
        config_seed["split_seed"] = 100
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_seed))

        # 5. Test shard_size sensitivity
        config_shard = self.base_config.copy()
        config_shard["shard_size"] = 10000
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_shard))

        # 6. Test sequence_length sensitivity
        config_seq = self.base_config.copy()
        config_seq["sequence_length"] = 1024
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_seq))

        # 7. Test cleaning_version sensitivity
        config_clean = self.base_config.copy()
        config_clean["cleaning_version"] = "gutenberg_cleaning_v2"
        self.assertNotEqual(base_hash, generate_content_hash(self.data_ids, config_clean))

    def test_tokenizer_identity_sensitivity(self):
        base_hash = generate_content_hash(self.data_ids, self.base_config)

        # Test tokenizer_identity changes content hash
        config_tok = self.base_config.copy()
        config_tok["tokenizer_identity"] = "different_tokenizer_sha256"
        tok_hash = generate_content_hash(self.data_ids, config_tok)
        self.assertNotEqual(base_hash, tok_hash)

        # Test tokenizer_config_identity changes content hash
        config_tok_cfg = self.base_config.copy()
        config_tok_cfg["tokenizer_config_identity"] = "different_config_sha256"
        tok_cfg_hash = generate_content_hash(self.data_ids, config_tok_cfg)
        self.assertNotEqual(base_hash, tok_cfg_hash)

    def test_manifest_identity(self):
        manifest_str = generate_manifest(self.stats, self.data_ids, self.base_config)
        manifest = json.loads(manifest_str)

        # Verify content_hash is exactly matching the computed hash
        expected_hash = generate_content_hash(self.data_ids, self.base_config)
        self.assertEqual(manifest["content_hash"], expected_hash)

        # Verify configuration identity is the SHA-256 of the configuration object
        expected_config_id = hashlib.sha256(json.dumps(self.base_config, sort_keys=True).encode()).hexdigest()
        self.assertEqual(manifest["dataset_config_identity"], expected_config_id)

    def test_missing_identity_raises_error(self):
        # 1. Test missing data_ids or config altogether
        with self.assertRaises(ValueError):
            generate_manifest(self.stats, None, self.base_config)
        with self.assertRaises(ValueError):
            generate_manifest(self.stats, self.data_ids, None)

        # 2. Test missing individual config elements
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
            bad_config = self.base_config.copy()
            del bad_config[key]
            with self.assertRaises(ValueError):
                generate_manifest(self.stats, self.data_ids, bad_config)

            # Test empty/None value raises error
            bad_config_none = self.base_config.copy()
            bad_config_none[key] = ""
            with self.assertRaises(ValueError):
                generate_manifest(self.stats, self.data_ids, bad_config_none)

    def test_deterministic_version(self):
        # Verify same inputs produce exactly the same version and config id
        m1 = json.loads(generate_manifest(self.stats, self.data_ids, self.base_config))
        m2 = json.loads(generate_manifest(self.stats, self.data_ids, self.base_config))

        self.assertEqual(m1["dataset_version"], m2["dataset_version"])
        self.assertTrue(m1["dataset_version"].startswith("1.0.0-"))
        self.assertEqual(m1["dataset_config_identity"], m2["dataset_config_identity"])

if __name__ == "__main__":
    unittest.main()
