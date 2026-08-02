import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from embedding_service import EmbeddingService

DB_PATH = os.path.join(os.path.dirname(__file__), 'nexa_vector_store.db')

class VectorStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()
        self.embedding_service = EmbeddingService()

    def _init_db(self):
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS documents (
                        doc_id TEXT PRIMARY KEY,
                        file_path TEXT,
                        file_name TEXT,
                        file_type TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id TEXT PRIMARY KEY,
                        doc_id TEXT,
                        content TEXT,
                        metadata TEXT,
                        embedding BLOB,
                        FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
                    );
                """)
                conn.commit()
        else:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT embedding FROM chunks LIMIT 1")
            except sqlite3.OperationalError:
                with sqlite3.connect(self.db_path) as conn:
                    conn.executescript("ALTER TABLE chunks ADD COLUMN embedding BLOB;")
                    conn.commit()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_document(self, doc_id: str, file_path: str, file_name: str, file_type: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO documents (doc_id, file_path, file_name, file_type) VALUES (?, ?, ?, ?)",
                (doc_id, file_path, file_name, file_type)
            )
            conn.commit()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_document(self, doc_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def clear(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            conn.commit()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                embedding = self.embedding_service.embed_text(chunk['content'])
                embedding_bytes = embedding.astype(np.float32).tobytes()
                
                cursor.execute(
                    "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, content, metadata, embedding) VALUES (?, ?, ?, ?, ?)",
                    (
                        chunk['chunk_id'], 
                        chunk['doc_id'], 
                        chunk['content'], 
                        json.dumps(chunk.get('metadata', {})),
                        embedding_bytes
                    )
                )
            conn.commit()

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_service.embed_text(query).astype(np.float32)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks")
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                if row['embedding']:
                    chunk_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                    sim = EmbeddingService.cosine_similarity(query_embedding, chunk_embedding)
                    
                    results.append({
                        'chunk_id': row['chunk_id'],
                        'doc_id': row['doc_id'],
                        'content': row['content'],
                        'metadata': json.loads(row['metadata']),
                        'similarity': float(sim)
                    })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            docs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunks = cursor.fetchone()[0]
            
            return {
                "document_count": docs,
                "chunk_count": chunks,
                "embedding_count": chunks
            }
