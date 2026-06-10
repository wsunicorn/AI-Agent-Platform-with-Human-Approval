const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export function createAgentRunSocket(runId: string) {
  return new WebSocket(`${WS_BASE_URL}/ws/agent-runs/${runId}`);
}

