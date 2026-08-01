import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'nexa_memory.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'memory_schema.sql')

class MemoryEngine:
    def __init__(self, db_path=DB_PATH, schema_path=SCHEMA_PATH):
        self.db_path = db_path
        self.schema_path = schema_path
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                with open(self.schema_path, 'r') as f:
                    conn.executescript(f.read())
                conn.commit()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Basic Memory Engine CRUD
    def create_memory(self, type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            metadata_str = json.dumps(metadata) if metadata else "{}"
            cursor.execute(
                "INSERT INTO memories (type, content, metadata) VALUES (?, ?, ?)",
                (type, content, metadata_str)
            )
            conn.commit()
            return cursor.lastrowid

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_memory(self, memory_id: int, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if content:
                cursor.execute("UPDATE memories SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (content, memory_id))
            if metadata:
                metadata_str = json.dumps(metadata)
                cursor.execute("UPDATE memories SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (metadata_str, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        # Simple keyword fallback implementation for Semantic Search
        with self._get_connection() as conn:
            cursor = conn.cursor()
            like_query = f"%{query}%"
            cursor.execute("SELECT * FROM memories WHERE content LIKE ? OR metadata LIKE ?", (like_query, like_query))
            return [dict(row) for row in cursor.fetchall()]

    def pin_memory(self, memory_id: int, is_pinned: bool = True) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memories SET is_pinned = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (1 if is_pinned else 0, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def archive_memory(self, memory_id: int, is_archived: bool = True) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memories SET is_archived = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (1 if is_archived else 0, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def merge_duplicates(self) -> int:
        # Placeholder for duplicate merging logic
        return 0

    # User Profile Operations
    def update_user_profile(self, profile_data: Dict[str, str]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users LIMIT 1")
            row = cursor.fetchone()
            if row:
                user_id = row['id']
                updates = []
                params = []
                for k, v in profile_data.items():
                    updates.append(f"{k} = ?")
                    params.append(v)
                if updates:
                    params.append(user_id)
                    query = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                    cursor.execute(query, params)
            else:
                columns = ', '.join(profile_data.keys())
                placeholders = ', '.join(['?'] * len(profile_data))
                params = list(profile_data.values())
                query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
                cursor.execute(query, params)
            conn.commit()

if __name__ == "__main__":
    engine = MemoryEngine()
    engine.create_memory("note", "Initialized Memory Engine")
    print("Memory Engine initialized successfully.")
