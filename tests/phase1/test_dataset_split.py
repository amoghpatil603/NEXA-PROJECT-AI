
import unittest
from backend.models.nexa_fm.data_pipeline.utils import deterministic_split

class TestSplit(unittest.TestCase):
    def test_reproducibility(self):
        ids = list(range(100))
        res1 = deterministic_split(ids, seed=42)
        res2 = deterministic_split(ids, seed=42)
        self.assertEqual(res1['train'], res2['train'])

    def test_no_overlap(self):
        ids = list(range(50))
        res = deterministic_split(ids, train_ratio=0.8, validation_ratio=0.1)
        overlap_train_val = set(res['train']) & set(res['validation'])
        overlap_train_test = set(res['train']) & set(res['test'])
        overlap_val_test = set(res['validation']) & set(res['test'])
        self.assertEqual(len(overlap_train_val), 0)
        self.assertEqual(len(overlap_train_test), 0)
        self.assertEqual(len(overlap_val_test), 0)
        self.assertEqual(len(res['train']) + len(res['validation']) + len(res['test']), 50)
