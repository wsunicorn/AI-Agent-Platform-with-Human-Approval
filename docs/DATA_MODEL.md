# Data Model

## Core Tables

### `tickets`

- `id`
- `source`
- `customer_name`
- `customer_email`
- `subject`
- `body`
- `status`
- `created_at`
- `updated_at`

### `agent_runs`

- `id`
- `mode`
- `input_type`
- `input_text`
- `status`
- `final_output`
- `created_by`
- `created_at`
- `completed_at`

### `tool_calls`

- `id`
- `agent_run_id`
- `tool_name`
- `sensitivity`
- `input_payload`
- `output_payload`
- `status`
- `error_message`
- `retry_count`
- `started_at`
- `completed_at`

### `approval_requests`

- `id`
- `agent_run_id`
- `tool_call_id`
- `tool_name`
- `proposed_payload`
- `edited_payload`
- `risk_reason`
- `status`
- `reviewer_id`
- `reviewer_comment`
- `created_at`
- `reviewed_at`
- `executed_at`

### `knowledge_documents`

- `id`
- `title`
- `content`
- `source`
- `tags`
- `document_type`
- `version`
- `checksum`
- `created_at`
- `updated_at`

### `knowledge_chunks`

- `id`
- `knowledge_document_id`
- `chunk_index`
- `content`
- `content_tsvector`
- `embedding`
- `embedding_model`
- `token_count`
- `metadata`
- `created_at`
- `updated_at`

### `model_configs`

- `id`
- `provider`
- `model_name`
- `endpoint_url`
- `mode`
- `purpose`
- `temperature`
- `max_tokens`
- `is_default`
- `created_at`
- `updated_at`

### `audit_logs`

- `id`
- `actor_type`
- `actor_id`
- `event_type`
- `entity_type`
- `entity_id`
- `before_state`
- `after_state`
- `metadata`
- `timestamp`

## Recommended Enums

### `agent_run.status`

- `queued`
- `running`
- `waiting_for_approval`
- `completed`
- `failed`
- `cancelled`

### `tool_calls.status`

- `proposed`
- `running`
- `completed`
- `failed`
- `denied`
- `waiting_for_approval`

### `approval_requests.status`

- `proposed`
- `pending_review`
- `approved`
- `rejected`
- `edited`
- `executed`
- `cancelled`
- `failed`

### `sensitivity`

- `safe`
- `approval_required`
- `blocked`

## Indexes

Recommended:

- `tickets(status, created_at)`
- `agent_runs(status, created_at)`
- `tool_calls(agent_run_id, created_at)`
- `approval_requests(status, created_at)`
- `audit_logs(entity_type, entity_id, timestamp)`
- `knowledge_chunks USING GIN(content_tsvector)`
- `knowledge_chunks USING hnsw(embedding vector_cosine_ops)`

## Data Rules

- Audit logs should be append-only.
- Approval edits must preserve the original proposed payload.
- Approved execution must use the final approved payload.
- Tool calls must store both success and failure attempts.
- Knowledge document updates should create new versions when policy text changes.

