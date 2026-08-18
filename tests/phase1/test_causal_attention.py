import unittest
import sys
import torch
from pathlib import Path

# Add path for models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models.nexa_fm.config import NexaFMConfig
from backend.models.nexa_fm.architecture import NexaFMModel

class TestCausalAttention(unittest.TestCase):
    def setUp(self):
        self.config = NexaFMConfig.tiny()
        self.model = NexaFMModel(self.config)
        self.model.eval()

    def test_causality_property(self):
        # Create a batch of size 2, sequence length 5
        # We will run two input tensors that differ only in the last token
        input1 = torch.tensor([[10, 20, 30, 40, 50],
                              [15, 25, 35, 45, 55]], dtype=torch.long)
        input2 = torch.tensor([[10, 20, 30, 40, 99], # modified 50 -> 99
                              [15, 25, 35, 45, 88]], dtype=torch.long) # modified 55 -> 88
        
        with torch.no_grad():
            logits1 = self.model(input1)
            logits2 = self.model(input2)
            
        # Logits shape is (B, T, V)
        # The logits for the first 4 tokens (index 0, 1, 2, 3) must be exactly identical
        # because future tokens (index 4) should not affect past tokens.
        diff = torch.abs(logits1[:, :4, :] - logits2[:, :4, :]).max().item()
        self.assertEqual(diff, 0.0, f"Causality broken! Past representations changed by future tokens: max diff={diff}")

    def test_combined_causal_and_padding_mask(self):
        # Batch size 2, sequence length 4
        # Second sequence has padding at the end
        input_ids = torch.tensor([[10, 20, 30, 40],
                                  [10, 20, 99, 99]], dtype=torch.long)
        # padding_mask: 1.0 (or True) for valid, 0.0 (or False) for padding
        padding_mask = torch.tensor([[True, True, True, True],
                                     [True, True, False, False]], dtype=torch.bool)
        
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask=padding_mask)
            
        # The first sequence is fully valid.
        # The second sequence has valid tokens at 0, 1, and padding at 2, 3.
        # Let's ensure the padding tokens do not cause NaN or incorrect gradients.
        self.assertFalse(torch.isnan(logits).any(), "NaN found in logits with padding mask")
        
    def test_sequence_length_1(self):
        # Test causality and stability on seq_len 1
        input_ids = torch.tensor([[10], [20]], dtype=torch.long)
        with torch.no_grad():
            logits = self.model(input_ids)
        self.assertEqual(logits.shape, (2, 1, self.config.vocab_size))

    def test_max_context_length(self):
        # Test model can run with max context length (using a tiny model config context length)
        seq_len = self.config.max_context_length
        input_ids = torch.ones((1, seq_len), dtype=torch.long) * 10
        with torch.no_grad():
            logits = self.model(input_ids)
        self.assertEqual(logits.shape, (1, seq_len, self.config.vocab_size))

if __name__ == "__main__":
    unittest.main()
