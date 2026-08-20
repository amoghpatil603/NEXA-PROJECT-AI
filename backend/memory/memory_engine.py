import json
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor
from backend.services.embedding_service import EmbeddingService
from backend.database.pg_database import get_connection, init_db, vector_to_sql_str

logger = logging.getLogger(__name__)

class MemoryEngine:
    def __init__(self, db_path=None):
        self.embedding_service = EmbeddingService()
        self._init_db()

    def _init_db(self):
        try:
            init_db()
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL schema in MemoryEngine: {e}")

    def _validate_user_id(self, user_id: str) -> str:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")
        return user_id.strip()

    # Basic Memory Engine CRUD using PostgreSQL & pgvector with Strict Isolation
    def create_memory(self, type: str, content: str, user_id: str, metadata: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> int:
        user_id = self._validate_user_id(user_id)
        embedding = self.embedding_service.embed_text(content)
        vec_str = vector_to_sql_str(embedding)
        meta = dict(metadata) if metadata else {}
        meta["user_id"] = user_id
        if session_id:
            meta["session_id"] = str(session_id).strip()
        meta_json = json.dumps(meta)

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO memories (type, content, metadata, embedding) VALUES (%s, %s, %s, %s::vector) RETURNING id",
                    (type, content, meta_json, vec_str)
                )
                memory_id = cursor.fetchone()[0]
            conn.commit()
            return memory_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error in MemoryEngine.create_memory: {e}")
            raise e
        finally:
            conn.close()

    def get_memory(self, memory_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        user_id = self._validate_user_id(user_id)
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, memory_uuid, type, content, importance, metadata, is_pinned, is_archived, created_at, updated_at FROM memories WHERE id = %s",
                    (memory_id,)
                )
                row = cursor.fetchone()
                if row:
                    res = dict(row)
                    meta = res.get('metadata')
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    res['metadata'] = meta or {}
                    # Strict isolation check
                    if res['metadata'].get('user_id') != user_id:
                        return None
                    res['created_at'] = str(res['created_at']) if res.get('created_at') else None
                    res['updated_at'] = str(res['updated_at']) if res.get('updated_at') else None
                    return res
                return None
        finally:
            conn.close()

    def update_memory(self, memory_id: int, user_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        user_id = self._validate_user_id(user_id)
        # First verify ownership
        existing = self.get_memory(memory_id, user_id)
        if not existing:
            return False

        conn = get_connection()
        try:
            updated = False
            with conn.cursor() as cursor:
                if content:
                    embedding = self.embedding_service.embed_text(content)
                    vec_str = vector_to_sql_str(embedding)
                    cursor.execute(
                        "UPDATE memories SET content = %s, embedding = %s::vector, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (content, vec_str, memory_id)
                    )
                    updated = cursor.rowcount > 0 or updated
                if metadata:
                    new_meta = dict(existing.get('metadata', {}))
                    new_meta.update(metadata)
                    new_meta['user_id'] = user_id
                    meta_json = json.dumps(new_meta)
                    cursor.execute(
                        "UPDATE memories SET metadata = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (meta_json, memory_id)
                    )
                    updated = cursor.rowcount > 0 or updated
            conn.commit()
            return updated
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False
        finally:
            conn.close()

    def delete_memory(self, memory_id: int, user_id: str) -> bool:
        user_id = self._validate_user_id(user_id)
        # Verify ownership before deletion
        existing = self.get_memory(memory_id, user_id)
        if not existing:
            return False

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()

    def search_memory(self, query: str, user_id: str, top_k: int = 5, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        user_id = self._validate_user_id(user_id)
        query_vec = self.embedding_service.embed_text(query)
        vec_str = vector_to_sql_str(query_vec)

        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, memory_uuid, type, content, importance, metadata, is_pinned, is_archived, created_at, updated_at,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM memories
                    WHERE is_archived = false AND embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT %s
                    """,
                    (vec_str, vec_str, top_k * 5)
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    d['similarity'] = float(d.get('similarity', 0.0))
                    meta = d.get('metadata')
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    d['metadata'] = meta or {}

                    # Strict isolation filter
                    if d['metadata'].get('user_id') != user_id:
                        continue
                    if session_id and d['metadata'].get('session_id') != session_id:
                        continue

                    d['created_at'] = str(d['created_at']) if d.get('created_at') else None
                    d['updated_at'] = str(d['updated_at']) if d.get('updated_at') else None
                    results.append(d)
                    if len(results) >= top_k:
                        break
                return results
        except Exception as e:
            logger.error(f"Error in search_memory pgvector query: {e}")
            return []
        finally:
            conn.close()

    def pin_memory(self, memory_id: int, user_id: str, is_pinned: bool = True) -> bool:
        user_id = self._validate_user_id(user_id)
        existing = self.get_memory(memory_id, user_id)
        if not existing:
            return False

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE memories SET is_pinned = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (is_pinned, memory_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()

    def archive_memory(self, memory_id: int, user_id: str, is_archived: bool = True) -> bool:
        user_id = self._validate_user_id(user_id)
        existing = self.get_memory(memory_id, user_id)
        if not existing:
            return False

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE memories SET is_archived = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (is_archived, memory_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()

    def merge_duplicates(self) -> int:
        return 0

    # User Profile Operations
    def update_user_profile(self, profile_data: Dict[str, str]):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users LIMIT 1")
                row = cursor.fetchone()
                if row:
                    user_id = row[0]
                    updates = []
                    params = []
                    for k, v in profile_data.items():
                        if k in ('name', 'email', 'preferences'):
                            updates.append(f"{k} = %s")
                            params.append(v)
                    if updates:
                        params.append(user_id)
                        query = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                        cursor.execute(query, params)
                else:
                    cols = [k for k in profile_data.keys() if k in ('name', 'email', 'preferences')]
                    if cols:
                        col_str = ', '.join(cols)
                        val_placeholders = ', '.join(['%s'] * len(cols))
                        params = [profile_data[k] for k in cols]
                        cursor.execute(f"INSERT INTO users ({col_str}) VALUES ({val_placeholders})", params)
            conn.commit()
        finally:
            conn.close()
