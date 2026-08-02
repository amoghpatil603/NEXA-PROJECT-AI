import os
import json
import numpy as np
from embedding_service import EmbeddingService
from chunk_manager import ChunkManager
from rag_engine import RAGEngine

def run_tests():
    print("--- Test Embedding Generation & Cosine Similarity ---")
    es = EmbeddingService()
    emb1 = es.embed_text("This is a test document.")
    emb2 = es.embed_text("This is another document.")
    sim = EmbeddingService.cosine_similarity(emb1, emb2)
    print(f"Similarity: {sim:.4f} - OK")

    print("--- Test Chunk Generation ---")
    cm = ChunkManager(chunk_size=512, overlap=64)
    doc = {
        'doc_id': 'test_id',
        'file_path': 'test.txt',
        'file_name': 'test.txt',
        'content': 'A' * 1000
    }
    chunks = cm.chunk_document(doc)
    print(f"Generated {len(chunks)} chunks - OK")
    assert len(chunks) > 0

    print("--- Test Vector Search ---")
    rag = RAGEngine()
    doc_id = rag.import_document("README.md", background=False)
    print("Document imported.")
    results = rag.store.search_chunks("What is this project about?", top_k=3)
    print(f"Found {len(results)} chunks.")
    assert len(results) > 0

    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
