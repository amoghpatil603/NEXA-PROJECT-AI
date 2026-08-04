import os
import threading
import uuid
from typing import List, Dict, Any, Optional
from document_parser import DocumentParser
from chunk_manager import ChunkManager
from vector_store import VectorStore
from embedding_service import EmbeddingService

class KnowledgeEngine:
    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = ChunkManager()
        self.store = VectorStore()
        self.embedding_service = EmbeddingService()
        self._indexing_jobs = {}

    def add_document(self, file_path: str, background: bool = False) -> str:
        """Parse, chunk, embed, and store a document (TXT, Markdown, PDF, DOCX)."""
        if background:
            job_id = str(uuid.uuid4())
            t = threading.Thread(target=self._process_document, args=(file_path, job_id))
            self._indexing_jobs[job_id] = "Running"
            t.start()
            return job_id
        else:
            return self._process_document(file_path)

    def _process_document(self, file_path: str, job_id: str = None) -> str:
        try:
            doc = self.parser.parse(file_path)
            existing = self.store.get_document(doc['doc_id'])
            if existing:
                self.store.delete_document(doc['doc_id'])
            
            self.store.add_document(doc['doc_id'], doc['file_path'], doc['file_name'], doc['file_type'])
            chunks = self.chunker.chunk_document(doc)
            self.store.add_chunks(chunks)
            
            if job_id:
                self._indexing_jobs[job_id] = "Completed"
            return doc['doc_id']
        except Exception as e:
            if job_id:
                self._indexing_jobs[job_id] = f"Failed: {str(e)}"
            raise e

    def remove_document(self, doc_id: str):
        """Remove a document and its associated chunks/embeddings."""
        self.store.delete_document(doc_id)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search and return top-K matching chunks."""
        return self.store.search(query_text, top_k=top_k)

    def reindex(self, file_path: str) -> str:
        """Re-index a document by removing existing and re-adding."""
        doc_id = hashlib_md5(file_path) if 'hashlib_md5' in globals() else None
        return self.add_document(file_path, background=False)

    def stats(self) -> Dict[str, Any]:
        """Return statistics on indexed documents, chunks, and embeddings."""
        return self.store.stats()

    # Aliases for backward compatibility with RAGEngine
    def import_document(self, file_path: str, background: bool = False):
        return self.add_document(file_path, background=background)

    def delete_document(self, doc_id: str):
        return self.remove_document(doc_id)

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats()

# Alias RAGEngine to KnowledgeEngine
RAGEngine = KnowledgeEngine
