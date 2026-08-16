
import unittest
import re
from backend.models.nexa_fm.data_pipeline.utils import generate_content_hash

class TestVersioning(unittest.TestCase):
    def setUp(self):
        self.data_ids = ['doc1', 'doc2', 'doc3']
        self.config = {'param1': 10, 'param2': 'test'}

    def test_determinism(self):
        h1 = generate_content_hash(self.data_ids, self.config)
        h2 = generate_content_hash(self.data_ids, self.config)
        self.assertEqual(h1, h2)

    def test_data_change(self):
        h1 = generate_content_hash(self.data_ids, self.config)
        h2 = generate_content_hash(['doc1', 'doc2', 'doc4'], self.config)
        self.assertNotEqual(h1, h2)

    def test_config_change(self):
        h1 = generate_content_hash(self.data_ids, self.config)
        h2 = generate_content_hash(self.data_ids, {'param1': 11, 'param2': 'test'})
        self.assertNotEqual(h1, h2)

    def test_sha256_format(self):
        h = generate_content_hash(self.data_ids, self.config)
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)
        self.assertTrue(re.match(r'^[a-f0-9]+$', h))

if __name__ == '__main__':
    unittest.main()
