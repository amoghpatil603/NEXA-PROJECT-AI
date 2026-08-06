import json
import os
import logging
from pathlib import Path
from datetime import datetime
from psycopg2.extras import RealDictCursor
from backend.database.pg_database import get_connection, init_db, vector_to_sql_str
from backend.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, base_path='/content/NEXA-PROJECT-AI/nexa/memory'):
        self.base_path = Path(base_path)
        self.embedding_service = EmbeddingService()
        try:
            init_db()
        except Exception as e:
            logger.error(f"Error initializing DB in MemoryManager: {e}")

    def _get_path(self, layer, identifier='default'):
        return self.base_path / layer / f'{identifier}.json'

    def save_memory(self, layer, data, identifier='default'):
        now_str = datetime.now().isoformat()
        record = {
            'timestamp': now_str,
            'data': data
        }

        # Store in PostgreSQL
        content = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        vec = self.embedding_service.embed_text(content)
        vec_str = vector_to_sql_str(vec)
        meta_json = json.dumps({"identifier": identifier, "data": data, "timestamp": now_str})

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO memories (memory_uuid, type, content, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT (memory_uuid) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (f"{layer}_{identifier}", layer, content, meta_json, vec_str)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving memory in PostgreSQL MemoryManager: {e}")
        finally:
            conn.close()

        # Local file write for backup
        try:
            path = self._get_path(layer, identifier)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(record, f, indent=2)
        except Exception:
            pass

        return True

    def load_memory(self, layer, identifier='default'):
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT metadata, created_at FROM memories WHERE memory_uuid = %s OR (type = %s AND metadata->>'identifier' = %s)",
                    (f"{layer}_{identifier}", layer, identifier)
                )
                row = cursor.fetchone()
                if row:
                    meta = row['metadata']
                    if isinstance(meta, str):
                        try: meta = json.loads(meta)
                        except Exception: meta = {}
                    return {
                        'timestamp': meta.get('timestamp', str(row.get('created_at', ''))),
                        'data': meta.get('data', {})
                    }
        except Exception as e:
            logger.error(f"Error loading memory from PostgreSQL: {e}")
        finally:
            conn.close()

        # File fallback
        path = self._get_path(layer, identifier)
        if not path.exists():
            return None
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def search_memory(self, query, layer='long_term'):
        results = []
        vec = self.embedding_service.embed_text(query)
        vec_str = vector_to_sql_str(vec)

        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT metadata, content
                    FROM memories
                    WHERE type = %s AND embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT 5
                    """,
                    (layer, vec_str)
                )
                rows = cursor.fetchall()
                for row in rows:
                    meta = row['metadata']
                    if isinstance(meta, str):
                        try: meta = json.loads(meta)
                        except Exception: meta = {}
                    data = meta.get('data', row['content'])
                    results.append(data)
        except Exception as e:
            logger.error(f"Error searching memory in PostgreSQL: {e}")
        finally:
            conn.close()

        if not results:
            path = self.base_path / layer
            query_words = query.lower().split()
            if path.exists():
                for file in path.glob('*.json'):
                    try:
                        with open(file, 'r') as f:
                            record = json.load(f)
                            content_str = str(record.get('data', '')).lower()
                            if any(word in content_str for word in query_words if len(word) > 2):
                                results.append(record['data'])
                    except Exception:
                        continue
        return results
