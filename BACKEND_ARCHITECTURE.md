# NEXA Backend Architecture

## Overview
NEXA utilizes a decoupled architecture where an Express.js gateway manages the frontend and orchestrates requests to a high-performance FastAPI service, with centralized persistence provided by PostgreSQL and pgvector.

## Core Modules

### 1. API Layer (`backend/api/`)
Handles HTTP communication and provides standard and streaming endpoints for chat, vision, and voice interactions.

### 2. Autonomous Agents (`backend/agents/`)
Implements the Agent Society, Planning Engines, and Execution Environments for multi-agent collaboration.

### 3. Memory System (`backend/memory/`)
Provides persistent memory and episodic memory capabilities using PostgreSQL (`nexa_db`) with vector search support via `pgvector`.

### 4. RAG Engine (`backend/rag/`)
Manages document chunking, embeddings, and similarity-based retrieval using PostgreSQL and pgvector.

### 5. Vision & Multimodal (`backend/vision/`)
Processes visual data through OCR engines and multimodal transformation pipelines.

### 6. Inference Engine (`backend/models/` & `backend/nexa/`)
Contains the Transformer Decoder architecture and provides quantized inference capabilities on CPU.
