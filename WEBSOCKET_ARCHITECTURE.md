# NEXA Platform v1.1.4 — WebSocket Real-Time Communication Architecture

## Overview

NEXA v1.1.4 upgrades the platform's communication layer to a production-grade, bi-directional WebSocket architecture built on Node.js and the `ws` library. The WebSocket server operates on port **3000** alongside the Express HTTP server and Vite application, providing real-time streaming capabilities without requiring external ports or structural alterations to existing APIs.

```
+-----------------------------------------------------------------------+
|                       NEXA Production Container                       |
|                                                                       |
|  +--------------------+        +-----------------------------------+  |
|  | React Client (SPA) | <----> | Express HTTP + WS Server (p3000)  |  |
|  | wsClient Handler   |  WS    |  - Connection Manager             |  |
|  +--------------------+ /ws    |  - Heartbeat & Ping/Pong          |  |
|                                |  - Chat WebSocket Stream          |  |
|                                |  - Voice WebSocket Engine         |  |
|                                |  - Studio Broadcast Engine        |  |
|                                +-----------------------------------+  |
|                                                  |                    |
|                                                  v (HTTP / Loopback)  |
|                                +-----------------------------------+  |
|                                |  Python FastAPI Service (p8000)   |  |
|                                |  - ChatEngine / PyTorch           |  |
|                                |  - RAG / Memory Engine (pgvector) |  |
|                                |  - Voice & Vision Services        |  |
|                                +-----------------------------------+  |
+-----------------------------------------------------------------------+
```

---

## Key Components

### 1. WebSocket Server (`server.ts`)
- **Transport**: Native WebSocket protocol (`ws://` / `wss://`) mounted on path `/ws` attached to the primary Node.js HTTP server.
- **Port**: Bound to `0.0.0.0:3000` to comply with single-port container routing constraints.
- **Heartbeat Monitoring**: 25-second ping/pong interval to detect silent TCP drops and purge stale socket handles.

### 2. Client Engine (`src/utils/websocketClient.ts`)
- **Singleton Client**: `NEXAWebSocketClient` handles auto-connection, authentication handshakes, and event dispatching.
- **Reconnection Logic**: Exponential backoff reconnect attempts (up to 10 retries) with status notifications (`connecting`, `connected`, `reconnecting`, `disconnected`).
- **Subscription Model**: Event-driven listeners for chat chunks, voice responses, and live Studio telemetry.

---

## Event Protocol Specification

### Authentication & Handshake
- **Client Handshake**:
  ```json
  { "type": "auth", "client_id": "client-1720000000", "token": "nexa-session-token" }
  ```
- **Server Acknowledgment**:
  ```json
  { "type": "connected", "client_id": "client-1720000000", "status": "authenticated", "message": "NEXA Real-Time WebSocket Server Connected" }
  ```

### Chat Streaming Protocol
- **Client Request (`chat_request`)**:
  ```json
  {
    "type": "chat_request",
    "request_id": "ws-req-1720000",
    "message": "Explain vector indexing",
    "system_prompt": "You are NEXA AI",
    "history": [],
    "max_tokens": 64,
    "temperature": 0.7
  }
  ```
- **Server Streaming Chunk (`chat_chunk`)**:
  ```json
  {
    "type": "chat_chunk",
    "request_id": "ws-req-1720000",
    "chunk": "Vector",
    "full": "Vector indexing allows...",
    "done": false
  }
  ```
- **Server Completion (`chat_done`)**:
  ```json
  {
    "type": "chat_done",
    "request_id": "ws-req-1720000",
    "full": "Vector indexing allows fast similarity search in pgvector.",
    "time_taken": 0.32,
    "tokens_per_sec": 78.5
  }
  ```

### Voice Streaming Protocol
- **Client Request (`voice_stream`)**:
  ```json
  { "type": "voice_stream", "request_id": "vreq-101", "text": "Execute system check" }
  ```
- **Server Response (`voice_response`)**:
  ```json
  { "type": "voice_response", "request_id": "vreq-101", "transcript": "Execute system check", "status": "ok", "reply_text": "NEXA Voice Engine: Received 'Execute system check'" }
  ```

### Studio Broadcast Protocol
- **Subscription (`studio_subscribe`)**: Registers socket for live 2-second telemetry broadcasts.
- **Telemetry Event (`studio_event` / `telemetry`)**:
  ```json
  {
    "type": "studio_event",
    "event_type": "telemetry",
    "data": {
      "ram_usage_mb": 142,
      "cpu_usage_pct": 16,
      "active_connections": 1,
      "total_inferences_completed": 5,
      "tokens_per_sec": 78.5
    }
  }
  ```

---

## Resilience & Fallback Architecture

If the WebSocket connection is degraded or fails:
1. Client automatically detects connection state.
2. `App.tsx` gracefully degrades to the Server-Sent Events (SSE) HTTP endpoint `/api/chat/stream`.
3. If SSE is unavailable, standard HTTP REST endpoint `/api/chat` completes the query.
4. No user intervention or refresh is required.
