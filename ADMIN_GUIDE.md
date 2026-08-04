# NEXA Platform - Administrator Guide

## Deployment & Hosting
NEXA is designed for isolated Docker deployment. 
Start the full stack: `docker-compose up -d --build`

## Configuration
- Environmental secrets must be injected into the `.env` file at the root of the project.
- Modify the `nginx.conf` file to configure HTTPS (SSL certs), custom domains, and cache rules.

## Monitoring
Check health status via `/api/health`.
Use `docker-compose logs -f` to monitor real-time output.
The Web Studio provides a high-level overview of system functionality and latency.

## Managing Data
- User uploads are stored in the `./uploads` directory.
- Model caches and memory DBs are stored in `./data`.
- To completely reset the environment, delete these mapped volume directories and restart the containers.
