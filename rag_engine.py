from document_parser import DocumentParser
from chunk_manager import ChunkManager
from vector_store import VectorStore
import threading
import uuid

class RAGEngine:
    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = ChunkManager()
        self.store = VectorStore()
        self._indexing_jobs = {}

    def import_document(self, file_path: str, background: bool = False):
        if background:
            job_id = str(uuid.uuid4())
            t = threading.Thread(target=self._process_document, args=(file_path, job_id))
            self._indexing_jobs[job_id] = "Running"
            t.start()
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
                self._indexing_jobs[job_id] = "Completed"
            return doc['doc_id']
        except Exception as e:
            if job_id:
                self._indexing_jobs[job_id] = f"Failed: {str(e)}"
            raise e

    def delete_document(self, doc_id: str):
        self.store.delete_document(doc_id)

    def get_statistics(self):
        return self.store.get_stats()
