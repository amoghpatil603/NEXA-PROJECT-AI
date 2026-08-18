import unittest
import sys
import json
from pathlib import Path
import torch

# Add path for models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tokenizer.incremental_bpe import IncrementalBPETokenizer
from backend.models.nexa_fm.config import NexaFMConfig
from backend.models.nexa_fm.architecture import NexaFMModel

class TestVocabCompatibility(unittest.TestCase):
    def test_vocab_size_contract(self):
        # 1. Load authoritative tokenizer config
        tok_config_path = Path(__file__).resolve().parent.parent.parent / "backend/tokenizer_v1/tokenizer_config.json"
        self.assertTrue(tok_config_path.exists(), "Tokenizer config not found at expected path")
        with open(tok_config_path, "r", encoding="utf-8") as f:
            tok_config = json.load(f)
        tok_vocab_size = tok_config["vocab_size"]

        # 2. Load tokenizer
        tok_path = Path(__file__).resolve().parent.parent.parent / "backend/tokenizer_v1/tokenizer.json"
        self.assertTrue(tok_path.exists(), "Tokenizer JSON not found at expected path")
        tokenizer = IncrementalBPETokenizer.load(tok_path)
        
        # Determine maximum valid token ID + 1
        # Token IDs should be in the range [0, vocab_size - 1]
        all_ids = list(tokenizer.vocab.keys())
        # Also check special tokens mapping values
        all_ids.extend(list(tokenizer.special_tokens.values()))
        max_token_id = max(all_ids)
        
        self.assertEqual(tok_vocab_size, max_token_id + 1, "Max token ID + 1 does not match vocab_size in config")

        # 3. Model Configuration
        config = NexaFMConfig()
        self.assertEqual(config.vocab_size, tok_vocab_size, "Model default vocab_size does not match tokenizer config")

        # 4. Instantiate model and verify embedding and LM head shapes
        model = NexaFMModel(config)
        self.assertEqual(model.embed_tokens.num_embeddings, config.vocab_size, "Embeddings size mismatch")
        self.assertEqual(model.lm_head.out_features, config.vocab_size, "LM head output projection size mismatch")

if __name__ == "__main__":
    unittest.main()
