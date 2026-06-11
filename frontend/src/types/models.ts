/** Domain model types matching backend SQLAlchemy models. */

export interface Ticket {
  id: string;
  subject: string;
  body: string;
  status: TicketStatus;
  priority: Priority;
  intent: string | null;
  customer_email: string | null;
  customer_name: string | null;
  channel: string;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  ticket_id: string | null;
  mode: AgentMode;
  status: AgentRunStatus;
  input_text: string;
  intent: string | null;
  priority: string | null;
  draft_response: string | null;
  final_output: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ToolCall {
  id: string;
  agent_run_id: string;
  tool_name: string;
  status: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown> | null;
  error_message: string | null;
  sensitivity: string | null;
  duration_ms: number | null;
  created_at: string;
}

export interface Approval {
  id: string;
  agent_run_id: string;
  tool_call_id: string | null;
  tool_name: string;
  status: ApprovalStatus;
  proposed_payload: Record<string, unknown>;
  edited_payload: Record<string, unknown> | null;
  risk_reason: string | null;
  reviewer: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  doc_type: string;
  status: string;
  tags: string[];
  source_url: string | null;
  chunk_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ModelConfig {
  id: string;
  provider: string;
  model_name: string;
  purpose: string;
  mode: string;
  is_default: boolean;
  is_enabled: boolean;
  config: Record<string, unknown>;
}

export interface ToolConfig {
  name: string;
  sensitivity: string;
  description: string | null;
  enabled: boolean;
}

export interface SearchResult {
  chunk_content: string;
  score: number;
  method: string;
  document_title: string | null;
  heading: string | null;
}

// Enums
export type TicketStatus = "new" | "triaged" | "in_progress" | "waiting_for_approval" | "resolved" | "closed";
export type Priority = "low" | "normal" | "high" | "urgent";
export type AgentMode = "support_agent" | "workflow_automation";
export type AgentRunStatus = "queued" | "running" | "waiting_for_approval" | "completed" | "failed" | "cancelled";
export type ApprovalStatus = "proposed" | "pending_review" | "approved" | "rejected" | "edited" | "executed" | "cancelled" | "failed";
export type Sensitivity = "safe" | "approval_required" | "blocked";
