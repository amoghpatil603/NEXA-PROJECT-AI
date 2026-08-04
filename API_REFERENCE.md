# NEXA API Reference

## Base URL
`https://ais-dev-s4mpunzdjwjn7pjjr6wkuh-752055184068.asia-southeast1.run.app/api`

## Endpoints

### 1. Health Check
- **GET `/api/health`**
- Returns platform operational status.

### 2. Inference & Execution
- **POST `/api/inference`**
- Headers: `Authorization: Bearer <JWT>`, `X-API-Key: <key>`
- Payload: `{"prompt": "string", "model_version": "v1.0-dpo"}`

### 3. Autonomous Workflows
- **POST `/api/workflows`**
- Payload: `{"name": "workflow_name", "tasks": [...]}`

### 4. Experience Analytics
- **GET `/api/experience/analytics`**
- Returns workflow success rates, tool reliability, and pattern mining metrics.
