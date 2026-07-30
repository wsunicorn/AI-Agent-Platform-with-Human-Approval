# Data Model

This reflects the actual schema in
`alembic/versions/20260610_0001_initial_schema.py` and the ORM models in
`app/models/`, not the original planning draft. All tables use a UUID primary
key (`id`) plus `created_at`/`updated_at` timestamps via shared mixins
(`app/models/mixins.py`) unless noted otherwise.

## Core Tables

### `tickets` (`app/models/ticket.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `source` | `varchar(64)` | Ingestion channel, e.g. `"web"`. |
| `customer_name` / `customer_email` | `varchar` | Nullable. |
| `subject` | `varchar(500)` | |
| `body` | `text` | |
| `status` | `ticket_status` enum | Default `new`. |
| `priority` | `priority` enum | Default `normal`. |
| `intent` | `varchar(128)` | Nullable; set once the agent classifies it. |
| `issue_type` | `varchar(128)` | Nullable. |
| `extracted_entities` | `jsonb` | Default `{}`. |
| `search_tsvector` | `tsvector`, **generated** | `to_tsvector('english', subject \|\| ' ' \|\| body)`, `GENERATED ALWAYS AS ... STORED`. |

### `agent_runs` (`app/models/agent_run.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `ticket_id` | `uuid`, FK → `tickets.id` | Nullable, `ON DELETE SET NULL`. |
| `mode` | `agent_mode` enum | `support_agent` \| `workflow_automation`. |
| `input_type` | `input_type` enum | `ticket` \| `email` \| `instruction`. |
| `input_text` | `text` | |
| `status` | `agent_run_status` enum | Default `queued`; see [derived status logic](#status-derivation) below. |
| `final_output` | `jsonb` | Nullable; rebuilt by `build_agent_run_output`. |
| `error_message` | `text` | Nullable. |
| `created_by` | `varchar(255)` | |
| `started_at` / `completed_at` | `timestamptz` | Nullable. |

### `tool_calls` (`app/models/tool_call.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `agent_run_id` | `uuid`, FK → `agent_runs.id` | `ON DELETE CASCADE`. |
| `tool_name` | `varchar(128)` | |
| `sensitivity` | `sensitivity` enum | Default `safe`. |
| `input_payload` / `output_payload` | `jsonb` | Input defaults `{}`; output nullable until completion. |
| `status` | `tool_call_status` enum | Default `proposed`. |
| `error_message` | `text` | Nullable. |
| `retry_count` | `integer` | Default `0`. |
| `timeout_ms` | `integer` | Nullable; set from `ToolExecutor.timeout_seconds` at call time. |
| `started_at` / `completed_at` | `timestamptz` | Nullable. |

### `approval_requests` (`app/models/approval_request.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `agent_run_id` | `uuid`, FK → `agent_runs.id` | `ON DELETE CASCADE`. |
| `tool_call_id` | `uuid`, FK → `tool_calls.id`, **unique** | One approval per tool call. `ON DELETE CASCADE`. |
| `tool_name` | `varchar(128)` | |
| `proposed_payload` | `jsonb` | Default `{}`; original payload, never mutated after creation. |
| `edited_payload` | `jsonb` | Nullable; set only if a reviewer edits before approving. |
| `risk_reason` | `text` | Required. |
| `status` | `approval_status` enum | Default `pending_review`. |
| `reviewer_id` / `reviewer_comment` | `varchar` / `text` | Nullable. |
| `reviewed_at` / `executed_at` | `timestamptz` | Nullable. |

### `knowledge_documents` (`app/models/knowledge.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `title` | `varchar(500)` | |
| `content` | `text` | Raw markdown. |
| `source` | `varchar(500)` | Nullable. |
| `tags` | `text[]` | Default `{}`. |
| `document_type` | `knowledge_document_type` enum | Default `policy`. |
| `version` | `integer` | Default `1`. Not currently incremented anywhere — ingestion always creates a new document row rather than a new version of an existing one. |
| `checksum` | `varchar(64)`, **unique** | SHA-256 of the content, used by `app/retrieval/ingestion.py` to reject duplicate uploads. |

### `knowledge_chunks` (`app/models/knowledge.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `knowledge_document_id` | `uuid`, FK → `knowledge_documents.id` | `ON DELETE CASCADE`. Unique together with `chunk_index`. |
| `chunk_index` | `integer` | |
| `content` | `text` | |
| `content_tsvector` | `tsvector`, **generated** | `to_tsvector('english', content)`, stored + GIN-indexed. |
| `embedding` | `vector(768)` | Nullable until embedded; dimension matches `local_embedding_dimensions` in `app/core/config.py`. |
| `embedding_model` | `varchar(255)` | Nullable. |
| `token_count` | `integer` | Nullable. |
| `metadata` (mapped as `chunk_metadata`) | `jsonb` | Default `{}`; holds `heading` (see `KnowledgeChunk.heading` property). |

### `model_configs` (`app/models/model_config.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `provider` | `model_provider` enum | `gemini` \| `openai` \| `anthropic` \| `ollama` \| `local`. |
| `model_name` | `varchar(255)` | |
| `endpoint_url` | `varchar(500)` | Nullable. |
| `mode` | `model_mode` enum | `hosted` \| `local`. |
| `purpose` | `model_purpose` enum | `default` \| `routing` \| `drafting` \| `embedding` \| `fallback` \| `quality`. |
| `temperature` | `float` | Default `0.2`. |
| `max_tokens` | `integer` | Default `2048`. |
| `is_default` | `boolean` | Default `false`. |
| Unique: `(provider, model_name, purpose)` | | |

**These rows are read/write through the `/settings/model-configs` API but are
not consulted by `app/llm/router.py`.** The router's provider/model fallback
chains are a hardcoded dict (`_DEFAULT_ROUTING`). Editing a model config
through the UI changes what is stored in Postgres, not what the agent
actually calls. See [`LLM_AND_RETRIEVAL.md`](LLM_AND_RETRIEVAL.md).

### `audit_logs` (`app/models/audit_log.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `actor_type` | `actor_type` enum | `human` \| `agent` \| `system` \| `tool`. |
| `actor_id` | `varchar(255)` | |
| `event_type` | `varchar(128)` | e.g. `tool_call.completed`, `approval.rejected`, `guardrail.denied`. |
| `entity_type` / `entity_id` | `varchar(128)` | |
| `before_state` / `after_state` | `jsonb` | Nullable snapshots. |
| `metadata` (mapped as `event_metadata`) | `jsonb` | Default `{}`. |
| `timestamp` | `timestamptz` | |

Rows are only ever inserted (`AuditService.record`); nothing in the codebase
updates or deletes an `audit_logs` row, so it is append-only in practice, not
just by convention.

## Enums

All twelve Postgres enums created by the initial migration (`app/models/enums.py`
is the Python-side source of truth):

| Enum | Values |
| --- | --- |
| `ticket_status` | `new`, `triaged`, `in_progress`, `waiting_for_approval`, `resolved`, `closed` |
| `priority` | `low`, `normal`, `high`, `urgent` |
| `agent_mode` | `support_agent`, `workflow_automation` |
| `input_type` | `ticket`, `email`, `instruction` |
| `agent_run_status` | `queued`, `running`, `waiting_for_approval`, `completed`, `failed`, `cancelled` |
| `sensitivity` | `safe`, `approval_required`, `blocked` |
| `tool_call_status` | `proposed`, `running`, `completed`, `failed`, `denied`, `waiting_for_approval` |
| `approval_status` | `proposed`, `pending_review`, `approved`, `rejected`, `edited`, `executed`, `cancelled`, `failed` |
| `actor_type` | `human`, `agent`, `system`, `tool` |
| `knowledge_document_type` | `policy`, `faq`, `playbook`, `macro`, `report_template` |
| `model_provider` | `gemini`, `openai`, `anthropic`, `ollama`, `local` |
| `model_mode` | `hosted`, `local` |
| `model_purpose` | `default`, `routing`, `drafting`, `embedding`, `fallback`, `quality` |

`approval_status.cancelled` is defined but never set by any code path — there
is no "cancel an approval request" action implemented in
`app/services/approval.py` or `app/api/approvals.py` today.

<a id="status-derivation"></a>
## How `agent_runs.status` is actually derived

`app/services/agent_run_summary.py:derive_agent_run_status` recomputes the
run's status from its child rows every time `refresh_agent_run_summary` runs
(after every approve/reject/edit/execute call, and lazily on `GET` list/detail
requests):

1. `CANCELLED` if the run was explicitly cancelled.
2. `RUNNING` if any `tool_calls` row is `running`.
3. `WAITING_FOR_APPROVAL` if any approval is `proposed`, `pending_review`,
   `approved`, or `edited` (i.e. not yet executed/rejected/failed).
4. `FAILED` if any tool call failed or any approval failed.
5. Otherwise `COMPLETED`.

`ticket_status_for_run` then maps that onto the parent ticket: `waiting_for_approval`
→ `WAITING_FOR_APPROVAL`, `completed` → `RESOLVED` **unless** the only outcome
was a rejected approval with no successful delivery (in which case the ticket
stays `IN_PROGRESS` so a rejected refund/email doesn't silently read as a
resolved ticket), `cancelled` → `TRIAGED`, anything else → `IN_PROGRESS`.

## Indexes

From the migration (not just "recommended" — these exist today):

- `tickets`: `(status, created_at)`, `(priority, created_at)`, GIN on `search_tsvector`.
- `agent_runs`: `(status, created_at)`, `(ticket_id, created_at)`.
- `tool_calls`: `(agent_run_id, created_at)`, `(status, created_at)`, `(tool_name, created_at)`.
- `approval_requests`: `(agent_run_id, created_at)`, `(status, created_at)`, unique `(tool_call_id)`.
- `audit_logs`: `(entity_type, entity_id, timestamp)`, `(event_type, timestamp)`.
- `knowledge_documents`: `(document_type, created_at)`.
- `knowledge_chunks`: `(knowledge_document_id)`, GIN on `content_tsvector`, partial
  HNSW on `embedding` (`vector_cosine_ops`, `m=16, ef_construction=64`,
  `WHERE embedding IS NOT NULL`).
- `model_configs`: `(provider, purpose, is_default)`.

## Seed Data

`app/db/seed.py` is idempotent (checked/rerunnable) and creates a demo refund
ticket, a support agent run waiting for approval, a safe draft-response tool
call plus an approval-required `send_email` tool call, a pending approval
request, two knowledge documents (English + the Vietnamese return-policy doc
in `docs/chinh_sach_doi_tra.md`) with their chunks, and model config rows for
Gemini/Ollama/router/quality/embedding purposes — used for display in
Settings, even though the router itself doesn't read them (see above).

## Data Rules

- Audit logs are append-only in practice (nothing updates/deletes them).
- Approval edits preserve `proposed_payload`; `edited_payload` is a separate
  column, so the diff view in the approval detail screen always has both
  sides to compare.
- `ToolExecutor.execute_approved` uses `approval_service.final_payload`, which
  prefers `edited_payload` over `proposed_payload`.
- Tool calls store both success and failure attempts; `retry_count` reflects
  actual attempts made by `RetryPolicy`, not a planned maximum.
- `knowledge_documents.version` and the "new version on policy change" idea
  from the original design are not implemented — re-ingesting changed content
  creates a new document row (or is rejected as a duplicate by the checksum
  constraint if content is unchanged).
