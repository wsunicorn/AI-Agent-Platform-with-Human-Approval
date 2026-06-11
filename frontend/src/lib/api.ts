/** Full API client for all backend endpoints. */

import type { ApiResponse } from "../types/api";
import type {
  AgentRun,
  Approval,
  AuditLog,
  KnowledgeDocument,
  ModelConfig,
  SearchResult,
  Ticket,
  ToolCall,
  ToolConfig,
} from "../types/models";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  const json = await res.json();
  return json.data ?? json;
}

// ── Health ────────────────────────────────────────────────────────

export async function getHealth() {
  const [live, ready] = await Promise.all([
    fetch(`${API_BASE}/health/live`).then((r) => r.json()),
    fetch(`${API_BASE}/health/ready`).then((r) => r.json()).catch(() => ({ status: "failed" })),
  ]);
  return { live: live.status, ready: ready.status, checks: ready.checks };
}

// ── Tickets ──────────────────────────────────────────────────────

export const fetchTickets = (params?: { status?: string; priority?: string; limit?: number; offset?: number }) => {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.priority) search.set("priority", params.priority);
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.offset) search.set("offset", String(params.offset));
  const qs = search.toString();
  return request<Ticket[]>(`/tickets${qs ? `?${qs}` : ""}`);
};

export const fetchTicket = (id: string) => request<Ticket>(`/tickets/${id}`);

export const createTicket = (body: { subject: string; body: string; customer_email?: string; customer_name?: string }) =>
  request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(body) });

export const updateTicket = (id: string, body: Record<string, unknown>) =>
  request<Ticket>(`/tickets/${id}`, { method: "PATCH", body: JSON.stringify(body) });

// ── Agent Runs ──────────────────────────────────────────────────

export const createSupportRun = (body: { input_text: string; ticket_id?: string }) =>
  request<AgentRun>("/agent-runs/support", { method: "POST", body: JSON.stringify(body) });

export const createWorkflowRun = (body: { input_text: string }) =>
  request<AgentRun>("/agent-runs/workflow", { method: "POST", body: JSON.stringify(body) });

export const fetchAgentRun = (id: string) => request<AgentRun>(`/agent-runs/${id}`);

export const fetchToolCalls = (runId: string) => request<ToolCall[]>(`/agent-runs/${runId}/tool-calls`);

export const cancelAgentRun = (id: string) =>
  request<AgentRun>(`/agent-runs/${id}/cancel`, { method: "POST" });

// ── Approvals ───────────────────────────────────────────────────

export const fetchApprovals = (params?: { status?: string; limit?: number }) => {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  return request<Approval[]>(`/approvals${qs ? `?${qs}` : ""}`);
};

export const fetchApproval = (id: string) => request<Approval>(`/approvals/${id}`);

export const approveAction = (id: string, body: { reviewer?: string; reason?: string }) =>
  request<Approval>(`/approvals/${id}/approve`, { method: "POST", body: JSON.stringify(body) });

export const rejectAction = (id: string, body: { reviewer?: string; reason?: string }) =>
  request<Approval>(`/approvals/${id}/reject`, { method: "POST", body: JSON.stringify(body) });

export const editAction = (id: string, body: { reviewer?: string; edited_payload: Record<string, unknown> }) =>
  request<Approval>(`/approvals/${id}/edit`, { method: "POST", body: JSON.stringify(body) });

export const executeAction = (id: string) =>
  request<Approval>(`/approvals/${id}/execute`, { method: "POST" });

// ── Knowledge ───────────────────────────────────────────────────

export const fetchDocuments = (params?: { doc_type?: string }) => {
  const search = new URLSearchParams();
  if (params?.doc_type) search.set("doc_type", params.doc_type);
  const qs = search.toString();
  return request<KnowledgeDocument[]>(`/knowledge-documents${qs ? `?${qs}` : ""}`);
};

export const createDocument = (body: { title: string; content: string; doc_type?: string; tags?: string[] }) =>
  request<KnowledgeDocument>("/knowledge-documents", { method: "POST", body: JSON.stringify(body) });

export const deleteDocument = (id: string) =>
  request<void>(`/knowledge-documents/${id}`, { method: "DELETE" });

export const searchKnowledge = (body: { query: string; doc_type?: string; limit?: number }) =>
  request<SearchResult[]>("/knowledge-documents/search", { method: "POST", body: JSON.stringify(body) });

// ── Audit Logs ──────────────────────────────────────────────────

export const fetchAuditLogs = (params?: { agent_run_id?: string; entity_type?: string; limit?: number }) => {
  const search = new URLSearchParams();
  if (params?.agent_run_id) search.set("agent_run_id", params.agent_run_id);
  if (params?.entity_type) search.set("entity_type", params.entity_type);
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  return request<AuditLog[]>(`/audit-logs${qs ? `?${qs}` : ""}`);
};

// ── Settings ────────────────────────────────────────────────────

export const fetchModelConfigs = () => request<ModelConfig[]>("/settings/model-configs");

export const createModelConfig = (body: Record<string, unknown>) =>
  request<ModelConfig>("/settings/model-configs", { method: "POST", body: JSON.stringify(body) });

export const fetchTools = () => request<ToolConfig[]>("/settings/tools");

export const fetchGuardrailPolicies = () => request<Record<string, unknown>>("/settings/guardrail-policies");
