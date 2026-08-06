# Background Jobs Report

## Overview
A scalable background job processor using Redis Queue (RQ) is now actively deployed across the NEXA AI service infrastructure.

## Moved Operations
- **Document Indexing**: File chunking, parsing, and vector embeddings generation have been moved out of the main request-response cycle and routed to RQ background workers.
- **Large File Processing**: Offloads large file reads directly to background jobs.

## Monitoring Endpoints
- `GET /queue/status`: Returns current queue length, failed jobs, finished jobs, and active workers.
- `GET /job/{job_id}`: Returns real-time execution status of an active or finished job.

## Resilience
Failed jobs are natively stored in the RQ failed registry, allowing subsequent inspection and retries.
