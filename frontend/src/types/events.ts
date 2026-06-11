/** WebSocket event types. */

export type WSEventType =
  | "agent_run.started"
  | "agent_run.step_started"
  | "agent_run.step_completed"
  | "agent_run.waiting_for_approval"
  | "agent_run.completed"
  | "agent_run.failed"
  | "tool_call.started"
  | "tool_call.completed"
  | "tool_call.failed"
  | "approval.created"
  | "approval.updated"
  | "approval.approved"
  | "approval.rejected"
  | "approval.executed"
  | "audit_log.created"
  | "notification.created"
  | "pong";

export interface WSEvent {
  type: WSEventType;
  data: Record<string, unknown>;
  timestamp?: string;
}
