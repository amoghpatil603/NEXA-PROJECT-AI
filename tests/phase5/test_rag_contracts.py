import unittest
from backend.rag.interfaces import Document, DocumentChunk, RetrievalResult, Retriever

class DeterministicInMemoryRetriever(Retriever):
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query: str, limit: int = 5):
        query_words = set(query.lower().split())
        results = []
        for chunk in self.chunks:
            chunk_words = set(chunk.text.lower().split())
            common = query_words.intersection(chunk_words)
            if common:
                score = float(len(common))
                citation = f"Doc: {chunk.document_id}, Chunk: {chunk.chunk_id}"
                results.append(RetrievalResult(chunk=chunk, score=score, citation=citation))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

class TestRAGContracts(unittest.TestCase):
    def test_valid_document_and_chunk(self):
        doc = Document(
            document_id="doc-1",
            text="NEXA AI is a powerful platform.",
            source="readme.md",
            metadata={"author": "Google Deepmind"}
        )
        self.assertEqual(doc.document_id, "doc-1")
        self.assertEqual(doc.text, "NEXA AI is a powerful platform.")
        self.assertEqual(doc.source, "readme.md")

        chunk = DocumentChunk(
            chunk_id="chunk-1-1",
            document_id="doc-1",
            text="NEXA AI is a powerful",
            metadata={"index": 0}
        )
        self.assertEqual(chunk.chunk_id, "chunk-1-1")
        self.assertEqual(chunk.document_id, "doc-1")

    def test_invalid_document_and_chunk(self):
        with self.assertRaises(ValueError):
            Document(document_id="", text="text", source="src")
        with self.assertRaises(ValueError):
            Document(document_id="id", text="", source="src")
        with self.assertRaises(ValueError):
            Document(document_id="id", text="text", source="")

        with self.assertRaises(ValueError):
            DocumentChunk(chunk_id="", document_id="doc", text="t")
        with self.assertRaises(ValueError):
            DocumentChunk(chunk_id="ch", document_id="", text="t")
        with self.assertRaises(ValueError):
            DocumentChunk(chunk_id="ch", document_id="doc", text="")

    def test_deterministic_retrieval(self):
        chunks = [
            DocumentChunk(chunk_id="c1", document_id="d1", text="The quick brown fox jumps over the lazy dog"),
            DocumentChunk(chunk_id="c2", document_id="d1", text="Artificial intelligence is transforming industries"),
            DocumentChunk(chunk_id="c3", document_id="d2", text="Transformers power modern large language models")
        ]
        retriever = DeterministicInMemoryRetriever(chunks)
        results = retriever.retrieve("transformers language models")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.chunk_id, "c3")
        self.assertGreater(results[0].score, 0.0)
        self.assertIn("d2", results[0].citation)

        results_empty = retriever.retrieve("completely unrelated words")
        self.assertEqual(len(results_empty), 0)

if __name__ == "__main__":
    unittest.main()
