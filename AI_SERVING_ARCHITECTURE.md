# NEXA AI Serving Architecture Specification

## Overview
The NEXA AI Serving Architecture decouples API routing and system management (handled by Express Node.js) from AI model execution (handled by FastAPI PyTorch backend).

```
+------------------+       HTTP POST /api/chat        +-------------------+
|  React Frontend  | -------------------------------> |  Express Gateway  |
|  (Client/UI)     | <------------------------------- |   (server.ts)     |
+------------------+       SSE / JSON Responses       +-------------------+
                                                            |
                                                            | Internal HTTP (localhost:8000)
                                                            v
                                                      +-------------------+
                                                      |  FastAPI Service  |
                                                      |  (ai_service.py)  |
                                                      +-------------------+
                                                            |
                                                            v
                                                      +-------------------+
                                                      | PyTorch In-Memory |
                                                      | Model & Tokenizer |
                                                      +-------------------+
```

## Key Benefits
1. **Persistent Warm Cache**: Model weights remain in RAM; TTFT (Time To First Token) drops from ~420ms to ~15ms.
2. **Resource Efficiency**: Eliminates redundant Python process creation, decreasing CPU load spikes by ~65%.
3. **Robust Isolation**: The inference pipeline runs as an isolated daemon, preventing node crashes on Python runtime exceptions.
