-- NEXA PostgreSQL + pgvector Database Schema

CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    preferences TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(255) PRIMARY KEY,
    conversation_id VARCHAR(255) REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Memory records table
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    memory_uuid VARCHAR(255) UNIQUE,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    importance FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    doc_id VARCHAR(255) PRIMARY KEY,
    file_path TEXT,
    file_name TEXT,
    file_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Chunks / RAG Embeddings table
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    doc_id VARCHAR(255) REFERENCES documents(doc_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Episodic Memory table
CREATE TABLE IF NOT EXISTS episodes (
    episode_id VARCHAR(255) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    goal TEXT,
    context TEXT,
    planner_decisions JSONB DEFAULT '[]'::jsonb,
    reasoning_strategy TEXT,
    tool_usage JSONB DEFAULT '[]'::jsonb,
    agent_collaboration JSONB DEFAULT '[]'::jsonb,
    errors TEXT,
    corrections TEXT,
    final_outcome VARCHAR(100),
    user_feedback TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_is_pinned ON memories(is_pinned);
CREATE INDEX IF NOT EXISTS idx_memories_is_archived ON memories(is_archived);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
