
import unittest
import json
from backend.models.nexa_fm.data_pipeline.utils import generate_manifest

class TestManifest(unittest.TestCase):
    def test_manifest_structure_and_values(self):
        stats = {
            'vocab_size': 8000,
            'train_tokens': 15000,
            'validation_tokens': 1500,
            'shard_count': 5,
            'max_length': 2048,
            'seed': 42,
            'hash': 'abc123hash',
            'train_documents': 10,
            'validation_documents': 2
        }
        
        data_ids = ["doc1", "doc2", "doc3"]
        dataset_config = {
            "train_ratio": 0.8,
            "validation_ratio": 0.1,
            "test_ratio": 0.1,
            "split_seed": 42,
            "shard_size": 50000,
            "sequence_length": 2048,
            "tokenizer_identity": "mock_tok_sha",
            "tokenizer_config_identity": "mock_config_sha",
            "cleaning_version": "mock_clean_v1"
        }

        manifest_json_str = generate_manifest(stats, data_ids, dataset_config)
        manifest = json.loads(manifest_json_str)

        # Verify keys
        expected_keys = [
            'dataset_name', 'dataset_version', 'tokenizer_version', 'vocab_size',
            'train_documents', 'validation_documents', 'train_tokens', 'validation_tokens',
            'shard_format', 'shard_count', 'sequence_length', 'split_seed', 'content_hash'
        ]
        for key in expected_keys:
            self.assertIn(key, manifest)

        # Verify uint16_binary constraint
        self.assertEqual(manifest['shard_format'], "uint16_binary")

        # Verify numerical integrity
        self.assertEqual(manifest['vocab_size'], 8000)
        self.assertEqual(manifest['train_tokens'], 15000)
        self.assertEqual(manifest['shard_count'], 5)

        from backend.models.nexa_fm.data_pipeline.utils import generate_content_hash
        expected_hash = generate_content_hash(data_ids, dataset_config)
        self.assertEqual(manifest['content_hash'], expected_hash)

if __name__ == '__main__':
    unittest.main()
