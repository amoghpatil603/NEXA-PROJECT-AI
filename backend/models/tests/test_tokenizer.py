"""
Unit tests for NexaBPETokenizer.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Ensure nexa-model is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS


class TestNexaBPETokenizer(unittest.TestCase):

    def setUp(self):
        self.sample_corpus = [
            "The quick brown fox jumps over the lazy dog.",
            "NEXA model tokenizer training for local AI.",
            "Hello world! Unicode test: 🚀 alpha beta gamma 🌟.",
        ]

    def test_ascii_round_trip(self):
        tok = NexaBPETokenizer(vocab_size=300, min_frequency=1)
        tok.train(self.sample_corpus)

        text = "The quick brown fox jumps over the lazy dog."
        encoded = tok.encode(text)
        decoded = tok.decode(encoded)
        self.assertEqual(text, decoded)

    def test_unicode_round_trip(self):
        tok = NexaBPETokenizer(vocab_size=300, min_frequency=1)
        tok.train(self.sample_corpus)

        text = "Hello world! Unicode test: 🚀 alpha beta gamma 🌟."
        encoded = tok.encode(text)
        decoded = tok.decode(encoded)
        self.assertEqual(text, decoded)

    def test_empty_input(self):
        tok = NexaBPETokenizer(vocab_size=300)
        self.assertEqual(tok.encode(""), [])
        self.assertEqual(tok.decode([]), "")

    def test_repeated_text(self):
        tok = NexaBPETokenizer(vocab_size=350, min_frequency=2)
        text = "banana " * 20
        tok.train([text])
        encoded = tok.encode(text)
        decoded = tok.decode(encoded)
        self.assertEqual(text, decoded)

    def test_special_control_tokens(self):
        tok = NexaBPETokenizer(vocab_size=300)
        text = "<NEXA_SYSTEM>You are NEXA.<NEXA_USER>Hi<NEXA_ASSISTANT>Hello!"
        encoded = tok.encode(text)

        # Check special token IDs appear in encoded output
        self.assertIn(DEFAULT_SPECIAL_TOKENS["<NEXA_SYSTEM>"], encoded)
        self.assertIn(DEFAULT_SPECIAL_TOKENS["<NEXA_USER>"], encoded)
        self.assertIn(DEFAULT_SPECIAL_TOKENS["<NEXA_ASSISTANT>"], encoded)

        decoded = tok.decode(encoded)
        self.assertEqual(text, decoded)

    def test_deterministic_training(self):
        tok1 = NexaBPETokenizer(vocab_size=320, min_frequency=2)
        tok1.train(self.sample_corpus)

        tok2 = NexaBPETokenizer(vocab_size=320, min_frequency=2)
        tok2.train(self.sample_corpus)

        self.assertEqual(tok1.merges, tok2.merges)
        self.assertEqual(tok1.vocab, tok2.vocab)

    def test_save_load_parity(self):
        tok = NexaBPETokenizer(vocab_size=320, min_frequency=1)
        tok.train(self.sample_corpus)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "tok.json"
            tok.save(save_path)

            loaded_tok = NexaBPETokenizer.load(save_path)

            text = "NEXA model tokenizer training for local AI."
            self.assertEqual(tok.encode(text), loaded_tok.encode(text))
            self.assertEqual(tok.decode(tok.encode(text)), loaded_tok.decode(loaded_tok.encode(text)))
            self.assertEqual(tok.merges, loaded_tok.merges)

    def test_malformed_tokenizer_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "bad.json"
            bad_path.write_text("{ invalid json", encoding="utf-8")

            with self.assertRaises(Exception):
                NexaBPETokenizer.load(bad_path)


if __name__ == "__main__":
    unittest.main()
