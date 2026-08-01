import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'nexa_vector_store.db')

class VectorStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

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
                        embedding TEXT,
                        FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
                    );
                """)
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

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                cursor.execute(
                    "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, content, metadata, embedding) VALUES (?, ?, ?, ?, ?)",
                    (
                        chunk['chunk_id'], 
                        chunk['doc_id'], 
                        chunk['content'], 
                        json.dumps(chunk.get('metadata', {})),
                        json.dumps(chunk.get('embedding', []))
                    )
                )
            conn.commit()

    def delete_document(self, doc_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def get_document(self, doc_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            like_query = f"%{query}%"
            cursor.execute("SELECT * FROM chunks WHERE content LIKE ? LIMIT ?", (like_query, top_k))
            return [dict(row) for row in cursor.fetchall()]
            
    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            return {"total_documents": doc_count, "total_chunks": chunk_count}
