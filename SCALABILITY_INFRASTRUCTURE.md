# Scalability Infrastructure

## Introduction
As part of v1.1.9, the NEXA platform introduced scalable decoupling between request processing and compute-heavy background workloads. 

## Key Improvements
- **Asynchronous Task Workers**: Background operations are routed to a scalable pool of RQ workers instead of blocking the main ASGI web server threads.
- **In-Memory Caching (Redis)**: Identical AI queries cache and return in O(1) time without triggering heavy neural network evaluation or duplicate downstream API calls.
- **Stateless HTTP**: By moving long-running tasks out of the HTTP thread and storing their intermediate statuses in Redis (`hset job_status`), API nodes remain stateless and can be scaled horizontally behind a load balancer without dropping critical document processing states.
