import unittest
import sys
import torch
from pathlib import Path

# Add path for models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models.nexa_fm.config import NexaFMConfig
from backend.models.nexa_fm.architecture import NexaFMModel, RotaryPositionalEmbedding, MultiHeadSelfAttention

class TestRoPE(unittest.TestCase):
    def test_rope_validation(self):
        # 1. Invalid head dimension (odd)
        config = NexaFMConfig(hidden_size=12, num_heads=5, use_rotary_embeddings=True)
        # head_dim will be 12 // 5 = 2. But 12 % 5 != 0, so it will raise ValueError
        with self.assertRaises(ValueError):
            MultiHeadSelfAttention(config)

        # 2. Invalid divisibility (hidden_size not divisible by num_heads)
        config = NexaFMConfig(hidden_size=10, num_heads=3, use_rotary_embeddings=True)
        with self.assertRaises(ValueError):
            MultiHeadSelfAttention(config)

        # 3. Valid config should pass without errors
        config = NexaFMConfig(hidden_size=128, num_heads=4, use_rotary_embeddings=True)
        attn = MultiHeadSelfAttention(config)
        self.assertEqual(attn.head_dim, 32)

    def test_max_context_length_check(self):
        config = NexaFMConfig(hidden_size=64, num_heads=4, max_context_length=32)
        model = NexaFMModel(config)
        
        # Passing input matching max context length should succeed
        input_ids = torch.ones((1, 32), dtype=torch.long)
        with torch.no_grad():
            model(input_ids)
            
        # Passing input exceeding max context length should fail with ValueError
        input_ids_overflow = torch.ones((1, 33), dtype=torch.long)
        with self.assertRaises(ValueError):
            with torch.no_grad():
                model(input_ids_overflow)

    def test_rope_numerical_determinism(self):
        # Initialize rotary positional embedding directly
        dim = 16
        rope = RotaryPositionalEmbedding(dim=dim, max_seq_len=64)
        
        dummy_tensor = torch.zeros(1, 1, 10, dim)
        emb1 = rope(dummy_tensor, seq_len=10)
        emb2 = rope(dummy_tensor, seq_len=10)
        
        # Test shape
        self.assertEqual(emb1.shape, (10, dim))
        
        # Test determinism
        torch.testing.assert_close(emb1, emb2)
        
        # Test specific sine/cosine relations
        cos1 = emb1.cos()
        sin1 = emb1.sin()
        
        # Cos^2 + Sin^2 should equal 1 for all elements
        identity_sum = cos1**2 + sin1**2
        ones = torch.ones_like(identity_sum)
        torch.testing.assert_close(identity_sum, ones)

if __name__ == "__main__":
    unittest.main()
