import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor
from backend.services.embedding_service import EmbeddingService
from backend.database.pg_database import get_connection, init_db, vector_to_sql_str

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, db_path=None):
        self._init_db()
        self.embedding_service = EmbeddingService()

    def _init_db(self):
        try:
            init_db()
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL schema in VectorStore: {e}")

    def add_document(self, doc_id: str, file_path: str, file_name: str, file_type: str):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (doc_id, file_path, file_name, file_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (doc_id) DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        file_name = EXCLUDED.file_name,
                        file_type = EXCLUDED.file_type
                    """,
                    (doc_id, file_path, file_name, file_type)
                )
            conn.commit()
        finally:
            conn.close()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT doc_id, file_path, file_name, file_type, created_at FROM documents WHERE doc_id = %s",
                    (doc_id,)
                )
                row = cursor.fetchone()
                if row:
                    res = dict(row)
                    res['created_at'] = str(res['created_at']) if res.get('created_at') else None
                    return res
                return None
        finally:
            conn.close()

    def delete_document(self, doc_id: str):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM chunks WHERE doc_id = %s", (doc_id,))
                cursor.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
            conn.commit()
        finally:
            conn.close()

    def clear(self):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM chunks")
                cursor.execute("DELETE FROM documents")
            conn.commit()
        finally:
            conn.close()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                for chunk in chunks:
                    embedding = self.embedding_service.embed_text(chunk['content'])
                    vec_str = vector_to_sql_str(embedding)
                    meta_json = json.dumps(chunk.get('metadata', {}))

                    cursor.execute(
                        """
                        INSERT INTO chunks (chunk_id, doc_id, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            doc_id = EXCLUDED.doc_id,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        (chunk['chunk_id'], chunk['doc_id'], chunk['content'], meta_json, vec_str)
                    )
            conn.commit()
        finally:
            conn.close()

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vec = self.embedding_service.embed_text(query)
        vec_str = vector_to_sql_str(query_vec)

        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT chunk_id, doc_id, content, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT %s
                    """,
                    (vec_str, vec_str, top_k)
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    meta = row['metadata']
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    results.append({
                        'chunk_id': row['chunk_id'],
                        'doc_id': row['doc_id'],
                        'content': row['content'],
                        'metadata': meta,
                        'similarity': float(row['similarity'])
                    })
                return results
        except Exception as e:
            logger.error(f"Error in search_chunks pgvector query: {e}")
            return []
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM documents")
                docs = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM chunks")
                chunks = cursor.fetchone()[0]

                return {
                    "document_count": docs,
                    "chunk_count": chunks,
                    "embedding_count": chunks
                }
        finally:
            conn.close()
