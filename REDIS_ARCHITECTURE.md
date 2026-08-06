# Redis Architecture & Integration

## Overview
Redis has been successfully integrated into the NEXA Platform to serve as an in-memory datastore for caching, queueing, and state management.

## Components
1. **Cache Storage**: Integrated in `/chat` for rapid inference retrieval of identical queries.
2. **Task Queues (RQ)**: Leveraged via Python `rq` to offload CPU-bound tasks like document parsing and chunk generation.
3. **Job Status Tracking**: Used `HSET/HGET` via `job_status` hash to securely report real-time status updates of asynchronous operations.

## Configuration
- Default connection to `localhost:6379` via `backend.utils.redis_client`.
- Robust fallback to standard synchronous execution if Redis is unavailable.
