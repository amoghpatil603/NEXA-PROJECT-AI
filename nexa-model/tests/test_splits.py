"""
Unit tests for data splitting and sharding.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).

Verifies small-corpus protection and deterministic splitting.
"""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.splits import split_documents
from data.sharding import create_shards, load_shard


class TestDataSplitsAndSharding(unittest.TestCase):

    def test_single_document_corpus(self):
        docs = [Path("doc1.txt")]
        splits = split_documents(docs)
        self.assertEqual(len(splits["train"]), 1)
        self.assertEqual(len(splits["val"]), 0)
        self.assertEqual(len(splits["test"]), 0)

    def test_two_document_corpus(self):
        docs = [Path("doc1.txt"), Path("doc2.txt")]
        splits = split_documents(docs)
        self.assertEqual(len(splits["train"]), 1)
        self.assertEqual(len(splits["val"]), 1)
        self.assertEqual(len(splits["test"]), 0)

    def test_three_document_corpus_small_protection(self):
        """
        Historical regression test: 3 documents with 80/10/10 ratio must NOT yield empty val or test splits.
        """
        docs = [Path("doc1.txt"), Path("doc2.txt"), Path("doc3.txt")]
        splits = split_documents(docs, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)

        self.assertEqual(len(splits["train"]), 1)
        self.assertEqual(len(splits["val"]), 1)
        self.assertEqual(len(splits["test"]), 1)

    def test_large_corpus_splitting(self):
        docs = [Path(f"doc_{i:03d}.txt") for i in range(100)]
        splits = split_documents(docs, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)

        self.assertEqual(len(splits["train"]), 80)
        self.assertEqual(len(splits["val"]), 10)
        self.assertEqual(len(splits["test"]), 10)

    def test_deterministic_seed(self):
        docs = [Path(f"doc_{i:03d}.txt") for i in range(20)]
        splits1 = split_documents(docs, seed=123)
        splits2 = split_documents(docs, seed=123)
        self.assertEqual(splits1, splits2)

    def test_sharding_round_trip(self):
        token_ids = list(range(1000))
        shard_size = 300

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            shard_paths = create_shards(token_ids, shard_size, out_dir)

            self.assertEqual(len(shard_paths), 4)

            reconstructed: List[int] = []
            for sp in shard_paths:
                reconstructed.extend(load_shard(sp))

            self.assertEqual(token_ids, reconstructed)


if __name__ == "__main__":
    unittest.main()
