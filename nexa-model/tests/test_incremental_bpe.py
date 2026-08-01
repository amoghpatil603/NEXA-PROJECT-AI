"""
Unit tests for IncrementalBPETokenizer reference parity.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

Verifies 100% exact output parity between reference NexaBPETokenizer
and IncrementalBPETokenizer.
"""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS
from tokenizer.incremental_bpe import IncrementalBPETokenizer


class TestIncrementalBPEParity(unittest.TestCase):

    def setUp(self):
        self.sample_corpus = [
            "The quick brown fox jumps over the lazy dog.",
            "NEXA model tokenizer training for local AI.",
            "Incremental BPE must maintain strict reference parity.",
            "Repeating words: banana banana apple apple cherry cherry.",
        ]

    def test_merge_sequence_and_vocab_parity(self):
        vocab_size = 350
        min_freq = 2

        ref_tok = NexaBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq, special_tokens=DEFAULT_SPECIAL_TOKENS)
        ref_tok.train(self.sample_corpus)

        inc_tok = IncrementalBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq, special_tokens=DEFAULT_SPECIAL_TOKENS)
        inc_tok.train(self.sample_corpus)

        # Merge sequence parity
        self.assertEqual(ref_tok.merges, inc_tok.merges, "Merge sequences do not match reference!")

        # Vocabulary parity
        self.assertEqual(ref_tok.vocab, inc_tok.vocab, "Vocabularies do not match reference!")

    def test_encoding_decoding_parity(self):
        vocab_size = 350
        min_freq = 2

        ref_tok = NexaBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq, special_tokens=DEFAULT_SPECIAL_TOKENS)
        ref_tok.train(self.sample_corpus)

        inc_tok = IncrementalBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq, special_tokens=DEFAULT_SPECIAL_TOKENS)
        inc_tok.train(self.sample_corpus)

        test_sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "NEXA model tokenizer training for local AI.",
            "Unseen text test with banana and apple.",
            "<NEXA_SYSTEM>System prompt test.<NEXA_USER>User query.<NEXA_ASSISTANT>Response.",
        ]

        for sentence in test_sentences:
            ref_encoded = ref_tok.encode(sentence)
            inc_encoded = inc_tok.encode(sentence)
            self.assertEqual(ref_encoded, inc_encoded, f"Encoded output mismatch for: {sentence}")

            ref_decoded = ref_tok.decode(ref_encoded)
            inc_decoded = inc_tok.decode(inc_encoded)
            self.assertEqual(ref_decoded, inc_decoded, f"Decoded output mismatch for: {sentence}")

    def test_save_load_incremental(self):
        inc_tok = IncrementalBPETokenizer(vocab_size=320, min_frequency=1)
        inc_tok.train(self.sample_corpus)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "inc_tok.json"
            inc_tok.save(save_path)

            loaded_tok = IncrementalBPETokenizer.load(save_path)

            text = "Incremental BPE save load test."
            self.assertEqual(inc_tok.encode(text), loaded_tok.encode(text))
            self.assertEqual(inc_tok.merges, loaded_tok.merges)


if __name__ == "__main__":
    unittest.main()
