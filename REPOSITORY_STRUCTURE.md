# NEXA Repository Structure

```
.
├── backend/                # Primary Python Backend
│   ├── api/                # FastAPI Endpoints & Runners
│   ├── agents/             # Agent Society & Execution Engines
│   ├── memory/             # Persistent & Episodic Memory Systems
│   ├── rag/                # RAG Engines & Vector Stores
│   ├── vision/             # OCR & Vision Pipelines
│   ├── services/           # core Business Logic & Platforms
│   ├── models/             # Transformer Architectures & Training
│   ├── utils/              # Shared Utilities & Tooling
│   ├── nexa/               # Core Inference Modules
│   └── tests/              # Backend Unit Tests
├── data/                   # Dataset & Upload Storage
├── src/                    # React Frontend Source
├── public/                 # Static Assets
├── dist/                   # Compiled Production Build
├── server.ts               # Express Gateway Server
├── package.json            # Node.js Dependencies
├── requirements.txt        # Python Dependencies
├── start.sh                # Container Entrypoint
└── prod_start.sh           # Production Startup Script
```
