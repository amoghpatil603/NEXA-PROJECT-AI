import os
import sys
import json
import sqlite3
import numpy as np
import logging
from pathlib import Path
from psycopg2.extras import RealDictCursor

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.pg_database import get_connection, init_db, vector_to_sql_str
from backend.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate_sqlite_memory(sqlite_path):
    if not os.path.exists(sqlite_path):
        logger.info(f"SQLite memory db not found at {sqlite_path}, skipping.")
        return 0

    logger.info(f"Migrating SQLite memory DB from {sqlite_path}...")
    conn_pg = get_connection()
    count = 0
    try:
        conn_sq = sqlite3.connect(sqlite_path)
        conn_sq.row_factory = sqlite3.Row
        cursor_sq = conn_sq.cursor()

        # Migrate memories
        cursor_sq.execute("SELECT * FROM memories")
        rows = cursor_sq.fetchall()
        embed_service = EmbeddingService()

        with conn_pg.cursor() as cursor_pg:
            for row in rows:
                r = dict(row)
                mem_type = r.get("type", "general")
                content = r.get("content", "")
                metadata = r.get("metadata", "{}")
                if isinstance(metadata, dict):
                    meta_json = json.dumps(metadata)
                else:
                    meta_json = metadata or "{}"

                is_pinned = bool(r.get("is_pinned", 0))
                is_archived = bool(r.get("is_archived", 0))
                created_at = r.get("created_at")
                updated_at = r.get("updated_at")

                emb_blob = r.get("embedding")
                if emb_blob:
                    try:
                        emb_arr = np.frombuffer(emb_blob, dtype=np.float32)
                    except Exception:
                        emb_arr = embed_service.embed_text(content)
                else:
                    emb_arr = embed_service.embed_text(content)

                vec_str = vector_to_sql_str(emb_arr)

                cursor_pg.execute(
                    """
                    INSERT INTO memories (type, content, metadata, embedding, is_pinned, is_archived)
                    VALUES (%s, %s, %s, %s::vector, %s, %s)
                    """,
                    (mem_type, content, meta_json, vec_str, is_pinned, is_archived)
                )
                count += 1

        # Migrate users
        try:
            cursor_sq.execute("SELECT * FROM users")
            user_rows = cursor_sq.fetchall()
            with conn_pg.cursor() as cursor_pg:
                for u in user_rows:
                    ud = dict(u)
                    cursor_pg.execute(
                        """
                        INSERT INTO users (name, email, preferences)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (email) DO UPDATE SET
                            name = EXCLUDED.name,
                            preferences = EXCLUDED.preferences
                        """,
                        (ud.get("name"), ud.get("email"), ud.get("preferences"))
                    )
        except Exception as ue:
            logger.warning(f"Note on user migration: {ue}")

        conn_pg.commit()
        conn_sq.close()
        logger.info(f"Successfully migrated {count} memory records from SQLite.")
    except Exception as e:
        conn_pg.rollback()
        logger.error(f"Error migrating SQLite memory db: {e}")
    finally:
        conn_pg.close()
    return count

def migrate_sqlite_vector_store(sqlite_path):
    if not os.path.exists(sqlite_path):
        logger.info(f"SQLite vector store db not found at {sqlite_path}, skipping.")
        return 0

    logger.info(f"Migrating SQLite vector store DB from {sqlite_path}...")
    conn_pg = get_connection()
    doc_count = 0
    chunk_count = 0
    try:
        conn_sq = sqlite3.connect(sqlite_path)
        conn_sq.row_factory = sqlite3.Row
        cursor_sq = conn_sq.cursor()
        embed_service = EmbeddingService()

        # Migrate documents
        try:
            cursor_sq.execute("SELECT * FROM documents")
            doc_rows = cursor_sq.fetchall()
            with conn_pg.cursor() as cursor_pg:
                for d in doc_rows:
                    dr = dict(d)
                    cursor_pg.execute(
                        """
                        INSERT INTO documents (doc_id, file_path, file_name, file_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (doc_id) DO UPDATE SET
                            file_path = EXCLUDED.file_path,
                            file_name = EXCLUDED.file_name,
                            file_type = EXCLUDED.file_type
                        """,
                        (dr.get("doc_id"), dr.get("file_path"), dr.get("file_name"), dr.get("file_type"))
                    )
                    doc_count += 1
        except Exception as de:
            logger.warning(f"Note on doc migration: {de}")

        # Migrate chunks
        try:
            cursor_sq.execute("SELECT * FROM chunks")
            chunk_rows = cursor_sq.fetchall()
            with conn_pg.cursor() as cursor_pg:
                for c in chunk_rows:
                    cr = dict(c)
                    chunk_id = cr.get("chunk_id")
                    doc_id = cr.get("doc_id")
                    content = cr.get("content", "")
                    metadata = cr.get("metadata", "{}")
                    if isinstance(metadata, dict):
                        meta_json = json.dumps(metadata)
                    else:
                        meta_json = metadata or "{}"

                    emb_blob = cr.get("embedding")
                    if emb_blob:
                        try:
                            emb_arr = np.frombuffer(emb_blob, dtype=np.float32)
                        except Exception:
                            emb_arr = embed_service.embed_text(content)
                    else:
                        emb_arr = embed_service.embed_text(content)

                    vec_str = vector_to_sql_str(emb_arr)

                    cursor_pg.execute(
                        """
                        INSERT INTO chunks (chunk_id, doc_id, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            doc_id = EXCLUDED.doc_id,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        (chunk_id, doc_id, content, meta_json, vec_str)
                    )
                    chunk_count += 1
        except Exception as ce:
            logger.warning(f"Note on chunk migration: {ce}")

        conn_pg.commit()
        conn_sq.close()
        logger.info(f"Successfully migrated {doc_count} docs and {chunk_count} chunks from SQLite.")
    except Exception as e:
        conn_pg.rollback()
        logger.error(f"Error migrating SQLite vector store db: {e}")
    finally:
        conn_pg.close()
    return chunk_count

def migrate_json_memories():
    logger.info("Migrating JSON memory stores...")
    conn_pg = get_connection()
    embed_service = EmbeddingService()
    count = 0

    json_files = [
        "memory_store.json",
        "memory_export.json",
    ]

    for jf in json_files:
        if os.path.exists(jf):
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        with conn_pg.cursor() as cursor_pg:
                            for item in data:
                                if isinstance(item, dict):
                                    mem_uuid = item.get("id", item.get("memory_uuid"))
                                    mem_type = item.get("type", "general")
                                    content = item.get("content", str(item.get("data", "")))
                                    importance = float(item.get("importance", 1.0))
                                    metadata = json.dumps(item.get("metadata", {}))
                                    vec = embed_service.embed_text(content)
                                    vec_str = vector_to_sql_str(vec)

                                    cursor_pg.execute(
                                        """
                                        INSERT INTO memories (memory_uuid, type, content, importance, metadata, embedding)
                                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                                        ON CONFLICT (memory_uuid) DO NOTHING
                                        """,
                                        (mem_uuid, mem_type, content, importance, metadata, vec_str)
                                    )
                                    count += 1
                        conn_pg.commit()
            except Exception as e:
                conn_pg.rollback()
                logger.error(f"Error migrating {jf}: {e}")

    # Also scan directory /content/NEXA-PROJECT-AI/nexa/memory or relative nexa/memory
    for dir_path in ["/content/NEXA-PROJECT-AI/nexa/memory", "nexa/memory", "backend/nexa/memory"]:
        p = Path(dir_path)
        if p.exists():
            for json_file in p.glob("**/*.json"):
                try:
                    with open(json_file, "r") as f:
                        rec = json.load(f)
                        data_content = rec.get("data", rec)
                        content_str = json.dumps(data_content) if isinstance(data_content, (dict, list)) else str(data_content)
                        layer = json_file.parent.name or "general"
                        identifier = json_file.stem
                        uuid_val = f"{layer}_{identifier}"
                        vec = embed_service.embed_text(content_str)
                        vec_str = vector_to_sql_str(vec)

                        with conn_pg.cursor() as cursor_pg:
                            cursor_pg.execute(
                                """
                                INSERT INTO memories (memory_uuid, type, content, metadata, embedding)
                                VALUES (%s, %s, %s, %s, %s::vector)
                                ON CONFLICT (memory_uuid) DO NOTHING
                                """,
                                (uuid_val, layer, content_str, json.dumps(rec), vec_str)
                            )
                            count += 1
                        conn_pg.commit()
                except Exception as e:
                    conn_pg.rollback()
                    logger.error(f"Error migrating file {json_file}: {e}")

    conn_pg.close()
    logger.info(f"Migrated {count} JSON memory items.")
    return count

def migrate_episodic_jsonl(jsonl_path="episodic_memory.jsonl"):
    if not os.path.exists(jsonl_path):
        logger.info(f"Episodic memory jsonl not found at {jsonl_path}, skipping.")
        return 0

    logger.info(f"Migrating episodic memory from {jsonl_path}...")
    conn_pg = get_connection()
    count = 0
    try:
        with open(jsonl_path, "r") as f:
            lines = f.readlines()

        with conn_pg.cursor() as cursor_pg:
            for line in lines:
                if line.strip():
                    ep = json.loads(line)
                    cursor_pg.execute(
                        """
                        INSERT INTO episodes (
                            episode_id, timestamp, goal, context, planner_decisions,
                            reasoning_strategy, tool_usage, agent_collaboration,
                            errors, corrections, final_outcome, user_feedback
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (episode_id) DO NOTHING
                        """,
                        (
                            ep.get("episode_id"),
                            ep.get("timestamp"),
                            ep.get("goal"),
                            str(ep.get("context", "")),
                            json.dumps(ep.get("planner_decisions", [])),
                            str(ep.get("reasoning_strategy", "")),
                            json.dumps(ep.get("tool_usage", [])),
                            json.dumps(ep.get("agent_collaboration", [])),
                            str(ep.get("errors", "")),
                            str(ep.get("corrections", "")),
                            str(ep.get("final_outcome", "")),
                            str(ep.get("user_feedback", ""))
                        )
                    )
                    count += 1
        conn_pg.commit()
        logger.info(f"Successfully migrated {count} episodic records.")
    except Exception as e:
        conn_pg.rollback()
        logger.error(f"Error migrating episodic jsonl: {e}")
    finally:
        conn_pg.close()
    return count

def run_full_migration():
    logger.info("Initializing PostgreSQL database schema...")
    init_db()

    c1 = migrate_sqlite_memory("backend/memory/nexa_memory.db")
    c2 = migrate_sqlite_vector_store("backend/rag/nexa_vector_store.db")
    c3 = migrate_json_memories()
    c4 = migrate_episodic_jsonl("episodic_memory.jsonl")

    logger.info("==================================================")
    logger.info("PostgreSQL Migration Complete Summary:")
    logger.info(f" - SQLite Memory Records: {c1}")
    logger.info(f" - SQLite Vector Store Chunks: {c2}")
    logger.info(f" - JSON Memory Items: {c3}")
    logger.info(f" - Episodic JSONL Records: {c4}")
    logger.info("==================================================")

if __name__ == "__main__":
    run_full_migration()
