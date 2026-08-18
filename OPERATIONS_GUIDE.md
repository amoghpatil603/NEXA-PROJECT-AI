# NEXA Operations Guide

## Monitoring & Observability
- **Prometheus Metrics**: Exported on `/metrics`.
- **Grafana Dashboards**: Visualize cluster resource utilization, request latency, and queue lengths.
- **Audit Logs**: Stored in `security_audit.jsonl` with real-time threat detection.

## Backup & Disaster Recovery
- **Scheduled Backups**: Automated daily snapshots of model registries, vector knowledge shards, and experience databases.
- **Restore Procedures**: Load checkpoint JSON files via the autonomous workflow manager upon container restart.
