# Core Backend Services

Phase 4 adds the backend runtime layer used by agent workflows, APIs, and the future
React dashboard.

## Services

### Config

`app.core.config.Settings` loads application, LLM, Redis event, retry, timeout, and
approval lock settings from environment variables.

### Database Session

`app.core.database.get_session` provides the FastAPI async SQLAlchemy session
dependency. Services flush changes but do not commit, so API routes and LangGraph
nodes can control transaction boundaries.

### Redis Client

`app.core.redis.get_redis` provides the shared Redis async client.

Redis is used for:

- Pub/Sub realtime events.
- Redis Streams event history.
- Sensitive action execution locks.

### Audit Service

`AuditService.record` writes append-only `audit_logs` rows and publishes an
`audit_log.created` event.

### Event Service

`EventService.publish` writes every event to Redis Streams and publishes it to:

- The global `humangate.events` channel.
- Optional topic channels such as `humangate.events.approvals`.

### WebSocket Manager

`WebSocketManager` tracks topic-based FastAPI WebSocket connections and can broadcast
JSON messages to active subscribers.

### Approval Service

`ApprovalService` owns approval state transitions:

- Create approval request.
- Approve.
- Edit and approve.
- Reject.
- Mark executed.
- Mark failed.

### Tool Registry

`ToolRegistry` stores registered tool definitions, including:

- Pydantic input schema.
- Pydantic output schema.
- Handler function.
- Sensitivity.
- Timeout and retry overrides.
- Risk reason.

### Tool Executor

`ToolExecutor` sends every proposed tool action through the guardrail policy engine,
validates tool input/output, writes `tool_calls`, enforces approval pauses for
approval-required tools, executes safe tools, blocks direct sensitive execution, and
records audit events.

### Retry and Timeout

`RetryPolicy` wraps async operations with:

- Max attempts.
- Per-attempt timeout.
- Exponential backoff.

### Redis Lock

`RedisLock` prevents duplicate execution of approved sensitive actions with a token
checked Lua release script.

## Current Smoke Test

The Phase 4 smoke path verifies:

- Safe tool executes immediately.
- Approval-required tool creates an approval request.
- Human approval changes state.
- Approved tool executes once under Redis lock.
- The test rolls back database changes after execution.
