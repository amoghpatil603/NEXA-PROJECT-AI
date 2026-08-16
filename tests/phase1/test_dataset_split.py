
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
        res = deterministic_split(ids, train_ratio=0.8)
        overlap = set(res['train']) & set(res['val'])
        self.assertEqual(len(overlap), 0)
        self.assertEqual(len(res['train']) + len(res['val']), 50)
