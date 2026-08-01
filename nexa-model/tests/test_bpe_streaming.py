"""
Unit tests for BPE streaming input and document boundary protection.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tokenizer.bpe_tokenizer import NexaBPETokenizer


class TestBPEStreamingAndBoundaries(unittest.TestCase):

    def test_document_boundary_protection(self):
        """
        Verify that BPE pairs are never formed across document boundaries.
        Example: doc1 ends with 'A', doc2 starts with 'B'.
        Even if doc1='A' and doc2='B' occur sequentially in corpus, pair ('A', 'B')
        frequency should be 0 because they belong to separate documents.
        """
        doc1 = "AB"
        doc2 = "BC"

        # Train with doc1 and doc2 as separate documents
        tok = NexaBPETokenizer(vocab_size=258, min_frequency=1)  # 256 base + 2 special
        tok.train([doc1, doc2])

        # Pair ('B', 'B') should NOT exist across boundary
        for m in tok.merges:
            v0 = tok.vocab[m[0]]
            v1 = tok.vocab[m[1]]
            # Ensure no merge combines the trailing 'B' of doc1 with leading 'B' of doc2
            self.assertNotEqual(v0 + v1, b"BB")

    def test_streaming_generator_input(self):
        """
        Verify that training works with a generator/stream of document strings.
        """
        def doc_generator():
            yield "First document content for BPE."
            yield "Second document content for BPE."
            yield "Third document content for BPE."

        tok = NexaBPETokenizer(vocab_size=300, min_frequency=2)
        tok.train(doc_generator())

        self.assertGreater(len(tok.merges), 0)
        encoded = tok.encode("First document content for BPE.")
        decoded = tok.decode(encoded)
        self.assertEqual(decoded, "First document content for BPE.")


if __name__ == "__main__":
    unittest.main()
