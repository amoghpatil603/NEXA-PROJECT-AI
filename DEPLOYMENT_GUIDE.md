# NEXA Platform Deployment Guide

## Overview
This guide provides instructions for deploying the NEXA Platform to a production environment. The platform includes a full-stack web application (React/Express/Python), a mobile application (Flutter), and an AI inference pipeline.

## Prerequisites
- Docker & Docker Compose
- Node.js 22.x
- Python 3.10+
- At least 16GB RAM for AI inference (GPU recommended)

## Architecture
The platform runs within a containerized environment:
1. **NGINX Reverse Proxy**: Handles incoming HTTP/HTTPS traffic, serves static assets, compresses responses, and proxies API requests.
2. **NEXA Application Server**: An Express server running Node.js that serves the React frontend and handles API logic. It spawns Python processes for ML tasks.
3. **Python AI Pipeline**: Executes LLM inference, RAG embeddings, and memory synchronization via local binaries.

## Deployment Steps

### 1. Clone & Configure
```bash
git clone <repository_url>
cd NEXA-PROJECT-AI
cp .env.example .env
# Edit .env with production secrets
```

### 2. Run with Docker Compose
The system is configured to launch securely via docker-compose:
```bash
docker-compose up -d --build
```
This will:
- Build the Node.js frontend/backend
- Install all Python dependencies inside the container
- Launch the reverse proxy on port 80
- Start the server on port 3000 (accessible internally)

### 3. Verify Deployment
Run the built-in health check:
```bash
curl -f http://localhost/api/health
```

### 4. Updating
To deploy updates:
```bash
git pull origin main
docker-compose up -d --build
```
