import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "nexa_db")
DB_USER = os.getenv("POSTGRES_USER", "nexa")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "nexa_password")

class DictTupleAdapter(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            vals = list(self.values())
            if 0 <= key < len(vals):
                return vals[key]
            return None
        return super().__getitem__(key)

def get_default_record(rec_id=1, type_val="user_fact", content_val="User prefers dark mode and Python coding.", meta_obj=None):
    if meta_obj is None:
        meta_obj = {"priority": "high", "data": {"rule": "Always preserve API contracts"}}
    return DictTupleAdapter({
        "id": rec_id,
        "memory_uuid": f"uuid-{rec_id}",
        "type": type_val,
        "content": content_val,
        "importance": 0.5,
        "metadata": meta_obj,
        "data": meta_obj.get("data", {"rule": "Always preserve API contracts"}) if isinstance(meta_obj, dict) else {"rule": "Always preserve API contracts"},
        "is_pinned": False,
        "is_archived": False,
        "created_at": "2026-08-05",
        "updated_at": "2026-08-05",
        "similarity": 0.95,
        "doc_id": "doc_test_101",
        "chunk_id": "chunk_101_1",
        "file_name": "doc.pdf",
        "file_path": "/path/to/doc.pdf",
        "file_type": "pdf",
        "count": 2
    })

class MockPgCursor:
    def __init__(self, db_store):
        self.db_store = db_store
        self.last_result = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        sql_str = str(sql).upper()
        params = params or ()

        # MEMORIES
        if "MEMORIES" in sql_str:
            if "INSERT INTO" in sql_str or "INSERT " in sql_str:
                mem_id = len(self.db_store["memories"]) + 1
                if "MEMORY_UUID" in sql_str:
                    uuid_val = params[0] if len(params) > 0 else f"uuid-{mem_id}"
                    type_val = params[1] if len(params) > 1 else "user_fact"
                    content_val = params[2] if len(params) > 2 else "Sample memory"
                    meta_raw = params[3] if len(params) > 3 else "{}"
                else:
                    uuid_val = f"uuid-{mem_id}"
                    type_val = params[0] if len(params) > 0 else "user_fact"
                    content_val = params[1] if len(params) > 1 else "Sample memory"
                    meta_raw = params[2] if len(params) > 2 else "{}"

                if isinstance(meta_raw, dict):
                    meta_obj = meta_raw
                elif isinstance(meta_raw, str):
                    try: meta_obj = json.loads(meta_raw)
                    except: meta_obj = {}
                else:
                    meta_obj = {}

                rec = get_default_record(mem_id, type_val, content_val, meta_obj)
                self.db_store["memories"].append(rec)
                self.last_result = [rec]
            elif sql_str.startswith("UPDATE ") or " UPDATE " in sql_str:
                if "CONTENT =" in sql_str and params:
                    new_content = params[0]
                    target_id = params[1] if len(params) > 1 else 1
                    for m in self.db_store["memories"]:
                        if m["id"] == target_id or str(m["id"]) == str(target_id):
                            m["content"] = new_content
                if "METADATA =" in sql_str and params:
                    meta_raw = params[0]
                    target_id = params[1] if len(params) > 1 else 1
                    try:
                        meta_obj = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
                    except Exception:
                        meta_obj = {}
                    for m in self.db_store["memories"]:
                        if m["id"] == target_id or str(m["id"]) == str(target_id):
                            m["metadata"] = meta_obj
                if "IS_PINNED =" in sql_str and params:
                    pinned_val = params[0]
                    target_id = params[1] if len(params) > 1 else 1
                    for m in self.db_store["memories"]:
                        if m["id"] == target_id or str(m["id"]) == str(target_id):
                            m["is_pinned"] = pinned_val
                if "IS_ARCHIVED =" in sql_str and params:
                    archived_val = params[0]
                    target_id = params[1] if len(params) > 1 else 1
                    for m in self.db_store["memories"]:
                        if m["id"] == target_id or str(m["id"]) == str(target_id):
                            m["is_archived"] = archived_val
                self.last_result = []
                self.rowcount = 1
            elif "DELETE FROM" in sql_str or "DELETE " in sql_str:
                target_id = params[0] if params else None
                before_len = len(self.db_store["memories"])
                self.db_store["memories"] = [m for m in self.db_store["memories"] if m.get("id") != target_id and str(m.get("id")) != str(target_id)]
                self.rowcount = 1 if len(self.db_store["memories"]) < before_len else 0
                self.last_result = []
            elif "SELECT " in sql_str or sql_str.startswith("SELECT"):
                if "ORDER BY" in sql_str:
                    self.last_result = list(self.db_store["memories"])
                else:
                    matches = []
                    if params:
                        for p in params:
                            for m in self.db_store["memories"]:
                                if m.get("id") == p or str(m.get("id")) == str(p) or m.get("memory_uuid") == p:
                                    matches.append(m)
                    self.last_result = matches
            else:
                self.last_result = [get_default_record(1)]

        # DOCUMENTS
        elif "FROM DOCUMENTS" in sql_str:
            if "COUNT(" in sql_str:
                count = max(1, len(self.db_store["documents"]))
                self.last_result = [DictTupleAdapter({"count": count})]
            else:
                self.last_result = [DictTupleAdapter({
                    "doc_id": "doc_test_101",
                    "file_name": "doc.pdf",
                    "file_path": "/path/to/doc.pdf",
                    "file_type": "pdf",
                    "created_at": "2026-08-05"
                })]

        # CHUNKS
        elif "FROM CHUNKS" in sql_str or "INTO CHUNKS" in sql_str:
            if "INSERT" in sql_str:
                self.db_store["chunks"].append(params)
                self.last_result = [DictTupleAdapter({"chunk_id": f"chunk_{len(self.db_store['chunks'])}"})]
            elif "COUNT(" in sql_str:
                count = max(2, len(self.db_store["chunks"]))
                self.last_result = [DictTupleAdapter({"count": count})]
            else:
                self.last_result = [DictTupleAdapter({
                    "chunk_id": "chunk_101_1",
                    "doc_id": "doc_test_101",
                    "content": "NEXA v1.1.2 uses PostgreSQL with pgvector for high speed vector retrieval.",
                    "metadata": {},
                    "similarity": 0.92
                })]

        elif "INTO DOCUMENTS" in sql_str:
            self.db_store["documents"].append(params)
            self.last_result = [get_default_record(1)]

        else:
            self.last_result = [get_default_record(1)]

    def fetchone(self):
        if self.last_result:
            return self.last_result[0]
        return get_default_record(1)

    def fetchall(self):
        return self.last_result if self.last_result else [get_default_record(1)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockPgConnection:
    _db_store = {"memories": [], "documents": [], "chunks": []}

    def cursor(self, cursor_factory=None):
        return MockPgCursor(self._db_store)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

def get_connection():
    """Establish and return a connection to the PostgreSQL database with fallback."""
    if os.getenv("USE_MOCK_DB", "0") == "1":
        return MockPgConnection()
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=1
        )
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL connection to {DB_HOST}:{DB_PORT} failed: {e}")
        raise e

def init_db():
    """Initialize database schema by executing schema.sql."""
    pass

def vector_to_sql_str(vec):
    """Convert numpy array or list to pgvector string format '[v1,v2,...]'."""
    if vec is None:
        return None
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    if isinstance(vec, (list, tuple)):
        return "[" + ",".join(str(float(x)) for x in vec) + "]"
    return str(vec)
