
import unittest
import json
from backend.models.nexa_fm.data_pipeline.utils import generate_manifest

class TestManifest(unittest.TestCase):
    def test_manifest_structure_and_values(self):
        stats = {
            'vocab_size': 8000,
            'train_tokens': 15000,
            'val_tokens': 1500,
            'shard_count': 5,
            'max_length': 2048,
            'seed': 42,
            'hash': 'abc123hash',
            'train_documents': 10,
            'val_documents': 2
        }
        
        manifest_json_str = generate_manifest(stats)
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
        self.assertEqual(manifest['content_hash'], 'abc123hash')

if __name__ == '__main__':
    unittest.main()
