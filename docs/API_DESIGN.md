# API Design

This lists the REST and WebSocket endpoints that actually exist in
`app/api/*.py`, mounted by `app/main.py`. There is no API versioning prefix
(no `/v1`); all routes hang directly off the app root except Settings.

## REST APIs

### Tickets (`app/api/tickets.py`, prefix `/tickets`)

```text
POST   /tickets                  create (source/channel, subject, body, customer_email?, customer_name?)
GET    /tickets                  list (?status, ?priority, ?limit, ?offset)
GET    /tickets/{ticket_id}
PATCH  /tickets/{ticket_id}      partial update (status?, priority?, assigned_to?)
```

### Agent Runs (`app/api/agent_runs.py`, prefix `/agent-runs`)

```text
POST   /agent-runs/support             start a support-agent run for a ticket (ticket_id?, input_text)
POST   /agent-runs/workflow            start a workflow-automation run (input_text)
GET    /agent-runs                     list (?ticket_id, ?status, ?limit, ?offset)
GET    /agent-runs/{run_id}
GET    /agent-runs/{run_id}/tool-calls
POST   /agent-runs/{run_id}/cancel
```

Both `POST` endpoints return `201` immediately with the run in `queued`
status; the actual LangGraph execution happens afterward in a FastAPI
`BackgroundTasks` coroutine in the same process (see
[`ARCHITECTURE.md`](ARCHITECTURE.md)). There is no `GET .../events` endpoint —
event history isn't queryable per run; use `/audit-logs?agent_run_id=...` or
the WebSocket channel instead. `POST /agent-runs/support` is idempotent per
ticket: if a live run already exists for that ticket (queued/running, or
waiting for approval), it's returned instead of starting a duplicate.

### Approvals (`app/api/approvals.py`, prefix `/approvals`)

```text
GET    /approvals                       list (?status, ?limit, ?offset)
GET    /approvals/{approval_id}
POST   /approvals/{approval_id}/approve   { reviewer?, reason? }
POST   /approvals/{approval_id}/reject    { reviewer?, reason? }
POST   /approvals/{approval_id}/edit      { reviewer?, edited_payload, reason? }
POST   /approvals/{approval_id}/execute   (no body)
```

`approve`/`reject`/`edit` go through `ApprovalService` under a row lock.
`execute` calls `ToolExecutor.execute_approved`, which takes a Redis lock,
re-checks the approval is `approved`/`edited` under the DB row lock, runs the
tool with the final (edited-or-proposed) payload, and marks the approval
`executed` or `failed`. There is no "cancel" endpoint — `ApprovalStatus.CANCELLED`
exists in the enum but nothing sets it.

### Knowledge Base (`app/api/knowledge.py`, prefix `/knowledge-documents`)

```text
POST   /knowledge-documents               create + ingest (title, content, doc_type?, tags?, source_url?)
GET    /knowledge-documents                list (?doc_type, ?limit, ?offset)
GET    /knowledge-documents/{document_id}
DELETE /knowledge-documents/{document_id}  204 No Content
POST   /knowledge-documents/search         hybrid search { query, doc_type?, limit? }
```

There is no `PATCH /knowledge-documents/{id}` and no `.../index` endpoint —
ingestion (chunking + embedding) happens synchronously inside the `POST`
handler (`app/retrieval/ingestion.py:ingest_document`), and documents are
immutable once created; to change content, delete and re-create. `doc_type`
must be one of the real `knowledge_document_type` enum values: `policy`,
`faq`, `playbook`, `macro`, `report_template`.

### Audit Logs (`app/api/audit_logs.py`, prefix `/audit-logs`)

```text
GET /audit-logs?agent_run_id={id}&entity_type={type}&actor_type={type}&action={event_type}&limit=&offset=
```

A single endpoint with query filters (all optional, combinable), not separate
routes per filter. The response also includes a server-rendered `message` and
`severity` (`info`/`success`/`warning`/`error`) per row, derived from
`event_type` for display in the Audit Log Explorer.

### Settings (`app/api/settings.py`, mounted under prefix `/settings`)

```text
GET    /settings/model-configs
POST   /settings/model-configs                   create (stored in DB; not read by the LLM router)
PATCH  /settings/model-configs/{config_id}

GET    /settings/tools                            derived from the tool registry + sensitivity catalog
PATCH  /settings/tools/{tool_name}                { sensitivity?, enabled? } — mutates the live catalog

GET    /settings/guardrail-policies                snapshot of safe/approval_required/blocked tool names
PATCH  /settings/guardrail-policies/{policy_id}    policy_id ∈ {safe_tools, approval_required_tools, blocked_tools}
                                                    body { tools: [...] } reassigns those tools' sensitivity
```

`PATCH /settings/tools/{tool_name}` and `PATCH /settings/guardrail-policies/{id}`
both write into `app/guardrails/catalog.py`'s shared, process-global
`TOOL_SENSITIVITY_CATALOG` dict — the same dict `PolicyEngine.decide` consults
on every tool call, so these edits take effect immediately for the running
process (and reset on restart; there is no persistence of catalog overrides).
`/settings/model-configs`, by contrast, only writes to Postgres for display —
`app/llm/router.py` does not read it (see [`LLM_AND_RETRIEVAL.md`](LLM_AND_RETRIEVAL.md)).

## WebSocket APIs

```text
GET /ws/agent-runs/{run_id}   agent-run-scoped event stream
GET /ws/approvals              all approval lifecycle events
GET /ws/notifications          every event, for a general activity feed
```

All three send `{"type": "pong"}` in reply to a client `"ping"` text frame
(sent every 30s by `ReconnectingWebSocket` to keep the connection alive); the
`pong` message otherwise carries no payload and should be ignored by UI logic
that reacts to real events. `/ws/approvals` and `/ws/notifications` are
implemented on the backend but the frontend does not currently open them — the
Approval Queue only polls REST every 5 seconds (see
[`FRONTEND_SPEC.md`](FRONTEND_SPEC.md)).

## Realtime Event Types

Emitted as `audit_log.created` envelopes and unwrapped by the WebSocket
listener into their original `event_type` before reaching the browser
(`app/api/websockets.py`):

```text
tool_call.started
tool_call.completed
tool_call.failed
approval.created
approval.approved
approval.edited
approval.rejected
approval.executed
approval.failed
guardrail.denied
ticket.seeded
```

There is no separate `agent_run.started` / `agent_run.step_*` event stream —
agent-run progress is inferred by the frontend re-fetching
`GET /agent-runs/{run_id}` and `.../tool-calls` whenever *any* event lands on
that run's WebSocket topic.

## Standard API Response Shape

Every REST response (success or error) uses this envelope
(`app/api/schemas.py:ApiResponse`), including error responses, which are
normalized by global exception handlers in `app/main.py` so `HTTPException`
and Pydantic validation failures both come back in this shape rather than
FastAPI's bare default `{"detail": "..."}`:

```json
{
  "data": {},
  "error": null,
  "meta": {}
}
```

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request payload is invalid.",
    "details": { "errors": [] }
  },
  "meta": {}
}
```

`code` is currently just `"HTTP_ERROR"` for any raised `HTTPException` (its
`status_code` still carries the real HTTP status) or `"VALIDATION_ERROR"` for
request-body validation failures — it is not yet a rich per-case error taxonomy.

## API Rules

- The client cannot execute approval-required tools directly; only
  `POST /approvals/{id}/execute` can, and only from `approved`/`edited` state.
- All JSON payloads are schema-validated with Pydantic.
- WebSocket events are a "something changed, go refetch" signal, not a
  payload of durable state — the client always re-reads via REST.
- There is no auth: any client can call any endpoint, and reviewer identity is
  whatever string the client sends (`reviewer`, defaulting to `"admin"` in the
  frontend). Do not deploy this beyond a local demo without adding one.
