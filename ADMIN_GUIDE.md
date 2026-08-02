# NEXA Administrator Guide

## Role-Based Access Control (RBAC)
NEXA enforces strict role permissions across five tiers:
- **Administrator**: Full administrative access across all subsystems, tools, and admin APIs.
- **Developer**: Access to memory, RAG, tools, Python execution, and agentic workflows.
- **Standard User**: Access to memory, RAG, tools, and agents.
- **Read Only**: View-only access to memory and RAG knowledge.
- **Service Account**: Automated pipeline access to tools, Python, and agents.

## Secret Management
All API keys, JWT secrets, and database credentials must be injected via environment variables or Kubernetes secrets. Never hardcode credentials.
