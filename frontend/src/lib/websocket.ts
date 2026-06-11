/** WebSocket client with auto-reconnect and event subscription. */

import type { WSEvent } from "../types/events";

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

type EventHandler = (event: WSEvent) => void;

export class ReconnectingWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private shouldReconnect = true;

  constructor(path: string) {
    this.url = `${WS_BASE}${path}`;
  }

  connect() {
    this.shouldReconnect = true;
    this._connect();
  }

  private _connect() {
    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this._startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WSEvent;
        this.handlers.forEach((handler) => handler(parsed));
      } catch {
        // Ignore malformed messages.
      }
    };

    this.ws.onclose = () => {
      this._stopPing();
      if (this.shouldReconnect) {
        this._scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private _scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this._connect();
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
    }, this.reconnectDelay);
  }

  private _startPing() {
    this._stopPing();
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 30000);
  }

  private _stopPing() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  disconnect() {
    this.shouldReconnect = false;
    this._stopPing();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Factory functions.
export const createAgentRunSocket = (runId: string) =>
  new ReconnectingWebSocket(`/ws/agent-runs/${runId}`);

export const createApprovalSocket = () =>
  new ReconnectingWebSocket("/ws/approvals");

export const createNotificationSocket = () =>
  new ReconnectingWebSocket("/ws/notifications");
