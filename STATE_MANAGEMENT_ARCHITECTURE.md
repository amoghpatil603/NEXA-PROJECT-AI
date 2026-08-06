# NEXA Platform v1.1.5 — Centralized State Management Architecture

## Overview

NEXA v1.1.5 introduces a centralized, reactive state management architecture built on **Zustand**. This architecture consolidates localized component state, prop drilling, and duplicate event subscriptions into a unified, high-performance state store while strictly preserving all existing backend APIs, WebSocket streams, and UI visual layouts.

```
+-----------------------------------------------------------------------------------+
|                            NEXA Centralized Store                                 |
|                            (useNexaStore - Zustand)                               |
|                                                                                   |
|  +------------------+  +------------------+  +-------------------+                |
|  |    Chat Slice    |  |  Session Slice   |  |  WebSocket Slice  |                |
|  | - chats          |  | - activeTab      |  | - wsStatus        |                |
|  | - activeChatId   |  | - user           |  | - wsClientId      |                |
|  | - isGenerating   |  | - modal states   |  | - latencyMs       |                |
|  +------------------+  +------------------+  +-------------------+                |
|                                                                                   |
|  +------------------+  +------------------+  +-------------------+                |
|  |   Studio Slice   |  | Monitoring Slice |  |    Voice Slice    |                |
|  | - activePage     |  | - telemetry      |  | - isRecording     |                |
|  | - agents         |  | - logs           |  | - transcript      |                |
|  +------------------+  +------------------+  +-------------------+                |
|                                                                                   |
|  +------------------+  +------------------+  +-------------------+                |
|  |   Vision Slice   |  | Notifications    |  |  Settings Slice   |                |
|  | - images         |  | - queue          |  | - settings        |                |
|  | - analysis       |  | - alerts         |  | - theme/prompt    |                |
|  +------------------+  +------------------+  +-------------------+                |
+-----------------------------------------------------------------------------------+
       ^                        ^                        ^
       | React Hooks            | React Hooks            | Event Subscriptions
       v                        v                        v
+------------------+    +------------------+    +-------------------+
|  App Workspace   |    | Studio Framework |    | WebSocket Client  |
| (Chat, Settings) |    | (Monitoring, AI) |    | (wsClient Engine) |
+------------------+    +------------------+    +-------------------+
```

---

## Architectural Principles

1. **Zero UI Redesign**: Preserves exact visual appearance, Tailwind styling, component dimensions, and animations.
2. **Zero Backend Alteration**: Works seamlessly with Express backend (`server.ts`), FastAPI services, and WebSocket streams without modifying any backend endpoints.
3. **Single Source of Truth**: Eliminates prop-drilling and duplicate local states across root `App.tsx`, `ChatView.tsx`, `VoiceRecorder.tsx`, `VisionUploader.tsx`, and Studio dashboards.
4. **Automatic WebSocket Synchronization**: Subscribes directly to `wsClient` status changes and telemetry events at the store level, updating reactive state automatically across all views.
5. **Persistence Integrity**: Synchronizes seamlessly with `localStorage` for chat history and user settings.
