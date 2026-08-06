# NEXA Platform Deployment Guide

## Prerequisites
- **Docker & Docker Compose**: For containerized deployment.
- **Redis Server**: Version 7+ required for caching and message queuing.
- **PostgreSQL**: Version 14+ required with `pgvector` extension.
- **Node.js**: v18+ for frontend build process.
- **Python**: v3.10+ for FastAPI inference services.

## Production Start Using Docker
1. Clone the repository and navigate to the project root.
2. Build the Docker container:
   ```bash
   docker build -t nexa-platform .
   ```
3. Boot the environment via Docker Compose:
   ```bash
   docker-compose up -d
   ```
   *(Alternatively, run `./start.sh` directly if on a bare-metal Linux server.)*

## Verifying Deployment
- **Frontend Dashboard**: Accessible via `http://localhost:3000`
- **FastAPI Backend**: Internal proxy listening via Express on port `3000/api`
- **WebSocket Streaming**: Available on `ws://localhost:3000/ws/telemetry`
- **Redis Job Monitor**: Status available on `http://localhost:3000/api/queue/status`
