# NEXA Operations Guide

## Daily Monitoring
1. **Studio Dashboard**: Check the `/studio/monitoring` page for CPU, memory, and inference throughput stats.
2. **Background Queues**: Use `GET /api/queue/status` to monitor pending or failed document processing tasks. If tasks pile up, horizontally scale the background workers.
3. **Database Health**: Regularly monitor PostgreSQL connection pooling and ensure the `pgvector` store is periodically vacuumed.

## Scaling Strategies
- **Web Nodes (Express)**: Horizontally scalable behind standard Load Balancers.
- **Inference Nodes (FastAPI)**: Keep stateless; scale according to GPU/CPU capabilities.
- **Redis Cache/Workers**: If inference limits are reached, boost Redis instance limits and spawn more RQ worker processes on independent pods.

## Troubleshooting
- **Redis Connection Errors**: Ensure `REDIS_HOST` and `REDIS_PORT` are configured correctly in `.env`.
- **Background Jobs Failing**: Inspect the RQ failed registry using `GET /api/job/{job_id}`.
- **Websocket Drops**: The frontend client (Zustand store) is configured to automatically backoff and reconnect.
