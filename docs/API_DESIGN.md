# API Design

## REST APIs

### Tickets

```text
POST /tickets
GET /tickets
GET /tickets/{ticket_id}
PATCH /tickets/{ticket_id}
```

### Agent Runs

```text
POST /agent-runs/support
POST /agent-runs/workflow
GET /agent-runs/{run_id}
GET /agent-runs/{run_id}/tool-calls
GET /agent-runs/{run_id}/events
POST /agent-runs/{run_id}/cancel
```

### Approvals

```text
GET /approvals
GET /approvals/{approval_id}
POST /approvals/{approval_id}/approve
POST /approvals/{approval_id}/reject
POST /approvals/{approval_id}/edit
POST /approvals/{approval_id}/execute
```

### Knowledge Base

```text
POST /knowledge-documents
GET /knowledge-documents
GET /knowledge-documents/{document_id}
PATCH /knowledge-documents/{document_id}
DELETE /knowledge-documents/{document_id}
POST /knowledge-documents/{document_id}/index
POST /knowledge-documents/search
```

### Audit Logs

```text
GET /audit-logs
GET /audit-logs?agent_run_id={run_id}
GET /audit-logs?entity_type=approval_request
GET /audit-logs?entity_type=tool_call
```

### Settings

```text
GET /model-configs
POST /model-configs
PATCH /model-configs/{config_id}

GET /tools
PATCH /tools/{tool_name}

GET /guardrail-policies
PATCH /guardrail-policies/{policy_id}
```

## WebSocket APIs

```text
GET /ws/agent-runs/{run_id}
GET /ws/approvals
GET /ws/notifications
```

## Realtime Event Types

- `agent_run.started`
- `agent_run.step_started`
- `agent_run.step_completed`
- `agent_run.waiting_for_approval`
- `agent_run.completed`
- `agent_run.failed`
- `tool_call.started`
- `tool_call.completed`
- `tool_call.failed`
- `approval.created`
- `approval.updated`
- `approval.approved`
- `approval.rejected`
- `approval.executed`
- `audit_log.created`
- `notification.created`

## Standard API Response Shape

```json
{
  "data": {},
  "error": null,
  "meta": {}
}
```

## Standard Error Shape

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request payload is invalid.",
    "details": {}
  },
  "meta": {}
}
```

## API Rules

- Client cannot execute approval-required tools directly.
- Approval execution must be checked server-side.
- All JSON payloads must be schema-validated.
- WebSocket events are for live UI updates, not durable state.
- The client should refetch durable state after reconnect.

