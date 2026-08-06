import logging
import os
import uuid
from backend.utils.document_parser import DocumentParser
from backend.utils.chunk_manager import ChunkManager
from backend.rag.vector_store import VectorStore
from backend.utils.redis_client import redis_conn

logger = logging.getLogger("nexa.background_jobs")

def process_document_job(file_path: str, job_id: str):
    logger.info(f"Starting background indexing job {job_id} for {file_path}")
    try:
        redis_conn.hset("job_status", job_id, "Running")
        parser = DocumentParser()
        chunker = ChunkManager()
        store = VectorStore()
        
        doc = parser.parse(file_path)
        
        existing = store.get_document(doc['doc_id'])
        if existing:
            store.delete_document(doc['doc_id'])
        
        store.add_document(doc['doc_id'], doc['file_path'], doc['file_name'], doc['file_type'])
        
        chunks = chunker.chunk_document(doc)
        store.add_chunks(chunks)
        
        redis_conn.hset("job_status", job_id, "Completed")
        logger.info(f"Completed background indexing job {job_id}")
        return doc['doc_id']
    except Exception as e:
        logger.error(f"Failed background indexing job {job_id}: {e}")
        redis_conn.hset("job_status", job_id, f"Failed: {str(e)}")
        # Raise exception to ensure RQ records the failure and retry mechanism can kick in
        raise e
