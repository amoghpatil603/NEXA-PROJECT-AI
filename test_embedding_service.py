import unittest
import numpy as np
from embedding_service import EmbeddingService

class TestEmbeddingService(unittest.TestCase):
    def setUp(self):
        self.service = EmbeddingService()

    def test_singleton(self):
        service2 = EmbeddingService()
        self.assertIs(self.service, service2)

    def test_embed_single(self):
        text = "Hello NEXA RAG system"
        vec = self.service.embed(text)
        self.assertIsInstance(vec, np.ndarray)
        self.assertEqual(vec.shape[0], 384)

    def test_embed_batch(self):
        texts = ["First document chunk", "Second document chunk"]
        embeddings = self.service.embedBatch(texts)
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape, (2, 384))

    def test_cosine_similarity(self):
        v1 = self.service.embed("Machine learning and AI")
        v2 = self.service.embed("Deep learning neural networks")
        v3 = self.service.embed("Baking chocolate chip cookies")
        
        sim_related = self.service.cosine_similarity(v1, v2)
        sim_unrelated = self.service.cosine_similarity(v1, v3)
        
        self.assertGreater(sim_related, sim_unrelated)

if __name__ == "__main__":
    unittest.main()
