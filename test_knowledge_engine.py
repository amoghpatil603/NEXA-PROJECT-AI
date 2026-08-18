import unittest
import os
import tempfile
from knowledge_engine import KnowledgeEngine

class TestKnowledgeEngine(unittest.TestCase):
    def setUp(self):
        self.engine = KnowledgeEngine()
        self.engine.store.clear() if hasattr(self.engine.store, 'clear') else None
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.txt_path = os.path.join(self.temp_dir.name, "test_doc.txt")
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("NEXA artificial intelligence and machine learning transformer architecture overview.")

        self.md_path = os.path.join(self.temp_dir.name, "test_doc.md")
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("# NEXA Markdown Guide\n\nRetrieval-Augmented Generation (RAG) combines search with LLM generation.")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_document_ingestion_and_chunking(self):
        doc_id = self.engine.add_document(self.txt_path)
        self.assertIsNotNone(doc_id)
        
        stats = self.engine.stats()
        self.assertEqual(stats["document_count"], 1)
        self.assertGreater(stats["chunk_count"], 0)
        self.assertGreater(stats["embedding_count"], 0)

    def test_markdown_ingestion(self):
        doc_id = self.engine.add_document(self.md_path)
        self.assertIsNotNone(doc_id)
        
        results = self.engine.query("Retrieval-Augmented Generation", top_k=1)
        self.assertGreater(len(results), 0)
        self.assertIn("RAG", results[0]["content"])

    def test_search_accuracy(self):
        self.engine.add_document(self.txt_path)
        self.engine.add_document(self.md_path)

        results = self.engine.query("machine learning transformer", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("transformer", results[0]["content"].lower())

    def test_document_removal(self):
        doc_id = self.engine.add_document(self.txt_path)
        self.assertEqual(self.engine.stats()["document_count"], 1)

        self.engine.remove_document(doc_id)
        self.assertEqual(self.engine.stats()["document_count"], 0)
        self.assertEqual(self.engine.stats()["chunk_count"], 0)

    def test_reindex(self):
        doc_id = self.engine.add_document(self.txt_path)
        initial_chunks = self.engine.stats()["chunk_count"]

        self.engine.reindex(self.txt_path)
        self.assertEqual(self.engine.stats()["chunk_count"], initial_chunks)

if __name__ == "__main__":
    unittest.main()
