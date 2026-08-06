# NEXA PostgreSQL + pgvector Storage Migration Report

## Overview
As part of the NEXA Platform infrastructure upgrade, all local SQLite and JSON memory/vector storage mechanisms have been migrated to PostgreSQL with `pgvector` enabled.

## 1. Database Schema Design

### Extension
- `pgvector` extension enabled via `CREATE EXTENSION IF NOT EXISTS vector;`

### Tables
1. **`users`**
   - `id SERIAL PRIMARY KEY`
   - `name VARCHAR(255)`
   - `email VARCHAR(255) UNIQUE`
   - `preferences TEXT`
   - `created_at / updated_at TIMESTAMP WITH TIME ZONE`

2. **`conversations`**
   - `id VARCHAR(255) PRIMARY KEY`
   - `title TEXT`
   - `user_id INT REFERENCES users(id)`
   - `metadata JSONB`
   - `created_at / updated_at TIMESTAMP WITH TIME ZONE`

3. **`messages`**
   - `id VARCHAR(255) PRIMARY KEY`
   - `conversation_id VARCHAR(255) REFERENCES conversations(id)`
   - `role VARCHAR(50)`
   - `content TEXT`
   - `metadata JSONB`
   - `embedding vector(384)`
   - `created_at TIMESTAMP WITH TIME ZONE`

4. **`memories`**
   - `id SERIAL PRIMARY KEY`
   - `memory_uuid VARCHAR(255) UNIQUE`
   - `type VARCHAR(100)`
   - `content TEXT`
   - `importance FLOAT`
   - `metadata JSONB`
   - `embedding vector(384)`
   - `is_pinned BOOLEAN`
   - `is_archived BOOLEAN`
   - `created_at / updated_at TIMESTAMP WITH TIME ZONE`

5. **`documents`**
   - `doc_id VARCHAR(255) PRIMARY KEY`
   - `file_path TEXT`
   - `file_name TEXT`
   - `file_type VARCHAR(100)`
   - `created_at TIMESTAMP WITH TIME ZONE`

6. **`chunks`**
   - `chunk_id VARCHAR(255) PRIMARY KEY`
   - `doc_id VARCHAR(255) REFERENCES documents(doc_id)`
   - `content TEXT`
   - `metadata JSONB`
   - `embedding vector(384)`
   - `created_at TIMESTAMP WITH TIME ZONE`

7. **`episodes`**
   - `episode_id VARCHAR(255) PRIMARY KEY`
   - `timestamp TIMESTAMP WITH TIME ZONE`
   - `goal TEXT`
   - `context TEXT`
   - `planner_decisions JSONB`
   - `reasoning_strategy TEXT`
   - `tool_usage JSONB`
   - `agent_collaboration JSONB`
   - `errors / corrections TEXT`
   - `final_outcome VARCHAR(100)`
   - `user_feedback TEXT`

## 2. Embedding Dimension & Search Mechanics
- **Vector Dimension**: 384 (matching `all-MiniLM-L6-v2` / NEXA default embedding service).
- **Distance Operator**: Cosine Distance `<=>`.
- **Similarity Score Calculation**: `1 - (embedding <=> %s::vector)`.
- **Performance**: HNSW index structures on vector columns for real-time similarity search.

## 3. Storage Abstraction Layer
The direct SQLite/JSON calls in the following modules have been updated to connect to PostgreSQL while preserving exact method signatures and return contracts:
- `backend/memory/memory_engine.py` -> `MemoryEngine`
- `backend/rag/vector_store.py` -> `VectorStore`
- `backend/memory/episodic_memory_engine.py` -> `EpisodicMemoryEngine`
- `backend/memory/nexa_memory_system.py` -> `MemoryStore` & `MemoryManager`
- `backend/nexa/memory/memory_manager.py` -> `NexaMemoryManager`

## 4. Migration Execution
- Migration script (`scripts/migrate_to_postgres.py`) executed successfully.
- Migrated data from SQLite databases (`nexa_memory.db`, `nexa_vector_store.db`), JSON stores (`memory_store.json`, `/content/NEXA-PROJECT-AI/nexa/memory/*.json`), and JSONL stores (`episodic_memory.jsonl`).
- Unit tests (`tests/test_postgres_memory_rag.py`) executed and passed 100%.

## Verification Status
- PostgreSQL Service: ACTIVE & HEALTHY
- Pgvector Extension: LOADED & FUNCTIONAL
- Unit & Integration Tests: 100% PASSED
