export type WSStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

export interface WSChatChunk {
  type: 'chat_chunk';
  request_id: string;
  chunk: string;
  full: string;
  done: boolean;
  time_taken?: number;
  tokens_per_sec?: number;
}

export interface WSChatDone {
  type: 'chat_done';
  request_id: string;
  full: string;
  time_taken: number;
  tokens_per_sec: number;
}

export interface WSVoiceResponse {
  type: 'voice_response';
  request_id: string;
  transcript: string;
  status: string;
  reply_text?: string;
}

export interface WSStudioEvent {
  type: 'studio_event';
  event_type: 'telemetry' | 'agent_progress' | 'task_execution' | 'notification';
  data: any;
}

type MessageHandler = (data: any) => void;

class NEXAWebSocketClient {
  private ws: WebSocket | null = null;
  private status: WSStatus = 'disconnected';
  private statusListeners: Set<(status: WSStatus) => void> = new Set();
  private messageListeners: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: any = null;
  private pingInterval: any = null;

  constructor() {
    // Auto-connect when in browser environment
    if (typeof window !== 'undefined') {
      this.connect();
    }
  }

  public getStatus(): WSStatus {
    return this.status;
  }

  public onStatusChange(listener: (status: WSStatus) => void): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  private setStatus(newStatus: WSStatus) {
    this.status = newStatus;
    this.statusListeners.forEach((fn) => fn(newStatus));
  }

  public connect() {
    if (typeof window === 'undefined') return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setStatus(this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[NEXA WS] Connected to WebSocket server');
        this.reconnectAttempts = 0;
        this.setStatus('connected');
        this.startHeartbeat();

        // Send auth handshake
        this.send({
          type: 'auth',
          client_id: `client-${Date.now()}`,
          token: 'nexa-session-token'
        });

        // Auto subscribe to studio events
        this.send({ type: 'studio_subscribe' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'ping') {
            this.send({ type: 'pong' });
            return;
          }

          // Trigger handlers for specific event type
          if (data.type) {
            const handlers = this.messageListeners.get(data.type);
            if (handlers) {
              handlers.forEach((fn) => fn(data));
            }
          }

          // Trigger general listeners
          const globalHandlers = this.messageListeners.get('*');
          if (globalHandlers) {
            globalHandlers.forEach((fn) => fn(data));
          }
        } catch (e) {
          console.error('[NEXA WS] Parse message error:', e);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[NEXA WS] WebSocket error:', err);
      };

      this.ws.onclose = () => {
        console.log('[NEXA WS] Connection closed');
        this.stopHeartbeat();
        this.setStatus('disconnected');
        this.scheduleReconnect();
      };
    } catch (err) {
      console.error('[NEXA WS] Connect error:', err);
      this.setStatus('disconnected');
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[NEXA WS] Max reconnect attempts reached');
      return;
    }

    const backoff = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 15000);
    this.reconnectAttempts++;
    console.log(`[NEXA WS] Scheduling reconnect in ${Math.round(backoff)}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, backoff);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 25000);
  }

  private stopHeartbeat() {
    if (this.pingInterval) clearInterval(this.pingInterval);
  }

  public send(data: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  public subscribe(eventType: string, handler: MessageHandler): () => void {
    if (!this.messageListeners.has(eventType)) {
      this.messageListeners.set(eventType, new Set());
    }
    this.messageListeners.get(eventType)!.add(handler);

    return () => {
      const handlers = this.messageListeners.get(eventType);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  public streamChat(
    payload: {
      request_id: string;
      message: string;
      system_prompt?: string;
      history?: any[];
      max_tokens?: number;
      temperature?: number;
    },
    onChunk: (chunk: WSChatChunk) => void,
    onDone: (done: WSChatDone) => void,
    onError?: (err: any) => void
  ): () => void {
    if (!this.send({ type: 'chat_request', ...payload })) {
      if (onError) onError(new Error('WebSocket not connected'));
      return () => {};
    }

    const unsubChunk = this.subscribe('chat_chunk', (data: WSChatChunk) => {
      if (data.request_id === payload.request_id) {
        onChunk(data);
      }
    });

    const unsubDone = this.subscribe('chat_done', (data: WSChatDone) => {
      if (data.request_id === payload.request_id) {
        onDone(data);
        cleanup();
      }
    });

    const unsubError = this.subscribe('chat_error', (data: any) => {
      if (data.request_id === payload.request_id) {
        if (onError) onError(new Error(data.error || 'Chat WS error'));
        cleanup();
      }
    });

    const cleanup = () => {
      unsubChunk();
      unsubDone();
      unsubError();
    };

    return () => {
      this.send({ type: 'chat_cancel', request_id: payload.request_id });
      cleanup();
    };
  }

  public sendVoiceStream(payload: { request_id: string; text: string; audio_data?: string }, callback: (res: WSVoiceResponse) => void) {
    this.send({ type: 'voice_stream', ...payload });
    const unsub = this.subscribe('voice_response', (data: WSVoiceResponse) => {
      if (data.request_id === payload.request_id) {
        callback(data);
        unsub();
      }
    });
  }

  public disconnect() {
    this.stopHeartbeat();
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('disconnected');
  }
}

export const wsClient = new NEXAWebSocketClient();
