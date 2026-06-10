# Architecture

![AI Agent Platform Architecture](assets/architecture-diagram-chatgpt-image.png)

## High-Level Architecture

```text
React Dashboard
  | REST
  | WebSocket
  v
FastAPI API
  | creates runs
  | manages approvals
  | serves audit logs
  v
LangGraph Workflow Runner
  | emits events
  | calls tools
  | requests approvals
  v
Guardrail Policy Engine
  | safe -> execute
  | approval_required -> approval queue
  | blocked -> deny
  v
Tool Executor
  | validates input/output
  | logs attempts
  v
Mock Integrations

PostgreSQL + pgvector stores durable state.
Redis Streams stores workflow events.
Redis Pub/Sub broadcasts live updates.
```

## Services

### `api`

Responsibilities:

- Expose REST APIs.
- Expose WebSocket endpoints.
- Create tickets and agent runs.
- Manage approvals.
- Serve audit logs.
- Authenticate and authorize users.

### `worker`

Responsibilities:

- Run long workflows.
- Execute background jobs.
- Run indexing jobs.
- Execute approved tools.
- Publish realtime events.

### `web`

Responsibilities:

- Render the React dashboard.
- Connect to REST APIs.
- Subscribe to WebSocket updates.
- Provide review and approval UI.

### `postgres`

Responsibilities:

- Store tickets, agent runs, tool calls, approvals, audit logs, documents, chunks, embeddings, and model configs.

### `redis`

Responsibilities:

- Pub/Sub for live dashboard updates.
- Streams for durable workflow events.
- Locks for duplicate-execution prevention.
- Short-lived progress state.

## Event Flow

```text
LangGraph node emits event
-> worker stores event if audit-relevant
-> worker writes event to Redis Stream
-> worker publishes event to Redis Pub/Sub
-> FastAPI WebSocket manager receives event
-> React dashboard updates live timeline
```

## Approval Execution Flow

```text
agent proposes action
-> policy engine classifies action
-> approval_required
-> approval request is saved
-> event is published
-> reviewer edits/approves/rejects
-> approved payload is locked
-> worker executes approved action
-> tool call and audit log are saved
```

## Architecture Rules

- The LLM may propose actions, but it never decides final execution permission.
- Policy decisions must happen in application code.
- All tool inputs and outputs must be Pydantic-validated.
- All sensitive actions must require server-side approval checks.
- Redis can accelerate realtime behavior, but PostgreSQL remains the source of truth.
- WebSocket reconnect must reload the latest durable state from PostgreSQL.
