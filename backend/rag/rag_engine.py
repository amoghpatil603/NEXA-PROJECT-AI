from backend.utils.document_parser import DocumentParser
from backend.utils.chunk_manager import ChunkManager
from backend.rag.vector_store import VectorStore
from backend.utils.redis_client import get_queue, redis_conn
from backend.utils.background_jobs import process_document_job
import uuid
import logging

class RAGEngine:
    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = ChunkManager()
        self.store = VectorStore()
        self.queue = get_queue()

    def import_document(self, file_path: str, background: bool = False):
        if background:
            job_id = str(uuid.uuid4())
            redis_conn.hset("job_status", job_id, "Pending")
            self.queue.enqueue(process_document_job, file_path, job_id, job_id=job_id)
            return job_id
        else:
            return self._process_document(file_path)

    def _process_document(self, file_path: str, job_id: str = None):
        try:
            doc = self.parser.parse(file_path)
            
            existing = self.store.get_document(doc['doc_id'])
            if existing:
                self.store.delete_document(doc['doc_id'])
            
            self.store.add_document(doc['doc_id'], doc['file_path'], doc['file_name'], doc['file_type'])
            
            chunks = self.chunker.chunk_document(doc)
            self.store.add_chunks(chunks)
            
            if job_id:
                redis_conn.hset("job_status", job_id, "Completed")
            return doc['doc_id']
        except Exception as e:
            if job_id:
                redis_conn.hset("job_status", job_id, f"Failed: {str(e)}")
            raise e

    def delete_document(self, doc_id: str):
        self.store.delete_document(doc_id)

    def get_statistics(self):
        return self.store.get_stats()
