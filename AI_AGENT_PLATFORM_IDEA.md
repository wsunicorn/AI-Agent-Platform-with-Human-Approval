# AI Agent Platform with Ticket Classification, Tool Calling, and Human Approval

## 1. Idea Review

### Current Strengths

This idea is strong because it solves a real adoption blocker for AI automation: companies want AI to reduce repetitive work, but they do not want the AI to independently perform sensitive actions such as sending emails, issuing refunds, deleting records, or changing customer/account data.

The concept is also portfolio-friendly because it combines several highly marketable AI engineering skills:

- LLM-based classification and extraction.
- Retrieval from policy documents or a knowledge base.
- Tool calling with structured inputs and outputs.
- Human-in-the-loop approval.
- Audit logging and compliance-oriented workflows.
- Retry, timeout, validation, and guardrail design.
- Dashboard or API-driven workflow orchestration.

### What Is Not Yet Optimized

The original idea is valuable, but it is slightly broad. It combines support automation, workflow automation, CRM updates, reporting, email drafting, refunds, task updates, and integrations. That is a good long-term platform vision, but too wide for a focused MVP.

The improved version should narrow the first product wedge:

> Build a support-operations AI agent that can classify tickets, retrieve policies, draft replies, create internal notes, and queue sensitive actions for human approval.

Workflow automation can still exist, but it should be treated as a secondary mode built on the same core system: tool registry, policy engine, approval queue, and audit log.

### Recommended Improvements

1. Make the human approval system the main differentiator, not just an optional step.
2. Define a clear action sensitivity model: safe, review-required, and blocked.
3. Add an approval state machine so every sensitive action has an explicit lifecycle.
4. Store every tool call with structured input, output, status, actor, timestamps, retry count, and error details.
5. Use mock integrations first, then design adapters for real services such as Zendesk, Gmail, Slack, HubSpot, or Salesforce.
6. Add evaluation criteria for classification accuracy, extraction accuracy, approval latency, and draft acceptance rate.
7. Build the MVP around customer support tickets before expanding into general workflow automation.
8. Use deterministic guardrails outside the LLM. The LLM may propose actions, but code-level policy gates must decide whether an action is auto-executable, approval-required, or forbidden.

## 2. Final Product Concept

### Product Name

HumanGate AI

### Case Study Title

AI Agent Platform with Ticket Classification, Tool Calling, and Human Approval

### One-Line Pitch

HumanGate AI is a support automation platform where AI agents classify tickets, retrieve policies, draft responses, and execute workflow tools while requiring human approval for sensitive actions.

### Product Positioning

Most companies do not reject AI automation because it is useless. They reject it because it can be risky. HumanGate AI solves this by giving teams AI speed with human control.

The system allows AI to handle low-risk work automatically, such as classification, summarization, knowledge base search, and draft creation. For high-risk operations, such as sending customer emails, issuing refunds, deleting data, or updating external systems, the agent must create an approval request and wait for a human reviewer.

## 3. Target Users

### Primary Users

- Customer support teams.
- Support operations managers.
- Small and mid-sized SaaS companies.
- E-commerce teams handling order, refund, and product issues.
- Agencies building AI workflow automation for clients.

### Secondary Users

- Customer success teams.
- Internal operations teams.
- AI automation consultants.
- CRM and helpdesk administrators.

## 4. Customer Problem

Support teams receive repetitive tickets every day, but many workflows still require human judgment. Teams want automation for routine work, but they are concerned about AI performing sensitive actions without review.

Common pain points:

- Agents spend too much time classifying tickets manually.
- Repetitive email replies slow down response time.
- Support notes and CRM updates are inconsistent.
- Policies are scattered across internal documents.
- Managers want automation but need auditability and control.
- AI tools often behave like black boxes.
- Sensitive actions require a clear approval trail.

## 5. Solution Overview

HumanGate AI receives a ticket, email, or instruction, analyzes it, retrieves relevant policy information, decides which tools to call, and produces a safe output.

The platform supports two modes:

### Mode 1: Support Agent Mode

Input:

- Support ticket.
- Customer email.
- Chat transcript.

Agent tasks:

- Classify intent.
- Detect priority.
- Extract entities.
- Retrieve relevant policy documents.
- Draft a customer response.
- Suggest internal notes.
- Recommend next actions.
- Queue sensitive actions for approval.

Example:

A customer writes:

> I want a refund for order #12345. The product arrived damaged.

The agent:

- Classifies intent as `refund_request`.
- Detects priority as `high`.
- Extracts order ID `12345`.
- Detects issue type `damaged_product`.
- Retrieves the refund and damaged-goods policy.
- Drafts a reply.
- Creates an approval request before sending the email or initiating a refund.

### Mode 2: Workflow Automation Mode

Input:

- Free-text instruction from a manager or operator.

Agent tasks:

- Convert the instruction into a structured plan.
- Select tools from the approved tool registry.
- Execute safe tools automatically.
- Queue sensitive actions for approval.
- Generate final artifacts such as reports, CRM notes, summaries, or email drafts.

Example:

A manager writes:

> Summarize all high-priority refund tickets from last week and draft a report.

The agent:

- Searches ticket data.
- Filters high-priority refund tickets.
- Summarizes recurring issues.
- Generates a report draft.
- Queues export or external sharing for approval if needed.

## 6. Core Differentiator

The product is not just an AI chatbot. It is an approval-first AI operations layer.

The key value is the ability to let AI work quickly while preventing unauthorized sensitive actions.

Core rule:

> The AI can recommend, draft, summarize, classify, and prepare. It cannot perform sensitive business actions unless a human approves them.

## 7. MVP Scope

### MVP Goal

Build a working platform that demonstrates AI-powered support ticket handling with tool calling, guardrails, audit logs, and human approval.

### MVP Must-Have Features

- Ticket/email/free-text input.
- Intent classification.
- Priority detection.
- Entity extraction.
- Knowledge base retrieval.
- Draft response generation.
- Tool registry.
- Tool input/output validation with Pydantic.
- Guardrail policy engine.
- Human approval queue.
- Audit log for every tool call.
- Retry and timeout handling.
- React web dashboard connected to the FastAPI backend.
- Mock integrations for email, CRM, refund, and ticket systems.

### MVP Should Not Include Yet

- Full multi-tenant billing.
- Real payment processor refunds.
- Full Zendesk/Salesforce production integration.
- Complex agent marketplace.
- Autonomous execution of sensitive tools.
- Large-scale analytics warehouse.
- Advanced role-based access control beyond basic reviewer/admin roles.

## 8. User Stories

### Support Agent

As a support agent, I want the system to classify a ticket and draft a reply so I can respond faster.

As a support agent, I want to edit the AI draft before approving it so I can keep the response accurate and human.

As a support agent, I want to see the policy sources used by the AI so I can verify its reasoning.

### Support Manager

As a support manager, I want sensitive actions to require approval so the AI cannot make risky business decisions alone.

As a support manager, I want audit logs for every tool call so I can investigate what happened.

As a support manager, I want weekly reports so I can understand support trends.

### Admin

As an admin, I want to define which tools are safe, sensitive, or blocked.

As an admin, I want to configure retry and timeout policies for tools.

As an admin, I want to connect knowledge base documents and mock external systems.

## 9. Action Sensitivity Model

Every tool has a sensitivity level.

### Safe Actions

Safe actions can run automatically.

Examples:

- Classify ticket.
- Extract entities.
- Search knowledge base.
- Summarize ticket.
- Draft email.
- Draft CRM note.
- Generate report draft.

### Approval-Required Actions

Approval-required actions must create an approval request before execution.

Examples:

- Send email to customer.
- Create or update CRM record.
- Change ticket status.
- Export report externally.
- Trigger refund request.
- Post to Slack channel.

### Blocked Actions

Blocked actions cannot be executed by the agent, even with approval, in the MVP.

Examples:

- Delete customer data.
- Issue actual refund through payment provider.
- Change billing plan.
- Access secrets or credentials.
- Modify audit logs.
- Disable guardrails.

## 10. Approval State Machine

Sensitive actions follow this lifecycle:

```text
proposed
-> pending_review
-> approved | rejected | edited
-> executed | cancelled | failed
```

### State Definitions

- `proposed`: The agent has suggested a sensitive action.
- `pending_review`: The action is waiting for human review.
- `approved`: A reviewer approved the action.
- `rejected`: A reviewer rejected the action.
- `edited`: A reviewer changed the action payload before approval.
- `executed`: The approved action was executed successfully.
- `cancelled`: The action was cancelled before execution.
- `failed`: Execution failed after approval.

### Approval Record Fields

- Approval ID.
- Ticket ID or workflow run ID.
- Tool name.
- Proposed input payload.
- Risk reason.
- Policy references.
- Created by agent ID.
- Reviewed by user ID.
- Status.
- Reviewer comment.
- Created timestamp.
- Reviewed timestamp.
- Executed timestamp.

## 11. Guardrail Rules

Guardrails must be implemented in application code, not only through prompting.

### Required Guardrails

- The agent cannot send email without approval.
- The agent cannot initiate refund without approval.
- The agent cannot delete customer data.
- The agent cannot modify audit logs.
- The agent cannot call tools outside the registered tool registry.
- The agent cannot execute a tool if Pydantic validation fails.
- The agent cannot execute a sensitive tool directly.
- Every tool call must be logged before and after execution.
- Every failed tool call must include an error reason.
- Timeout and retry policies must be enforced per tool.

### Example Policy Decision

```text
Tool: draft_email
Sensitivity: safe
Decision: auto_execute

Tool: send_email
Sensitivity: approval_required
Decision: create_approval_request

Tool: delete_customer_record
Sensitivity: blocked
Decision: deny
```

## 12. Agent Workflow

### Support Ticket Workflow

```text
1. Receive ticket or email.
2. Normalize input.
3. Classify intent.
4. Detect priority.
5. Extract entities.
6. Retrieve policy documents.
7. Draft customer response.
8. Recommend internal note.
9. Plan next actions.
10. Run safe tools automatically.
11. Create approval requests for sensitive tools.
12. Human reviewer approves, edits, or rejects.
13. Execute approved actions.
14. Write audit logs.
15. Return final result.
```

### Workflow Automation Flow

```text
1. Receive manager instruction.
2. Parse instruction into goal and constraints.
3. Generate action plan.
4. Validate selected tools.
5. Execute safe tools.
6. Queue sensitive tools for approval.
7. Generate final output.
8. Log every step.
```

## 13. Tool Registry

The platform should expose tools through a controlled registry.

### Tool Metadata

Each tool should define:

- Tool name.
- Description.
- Input schema.
- Output schema.
- Sensitivity level.
- Timeout seconds.
- Max retry count.
- Owner.
- Enabled/disabled status.

### Initial MVP Tools

#### `classify_ticket`

Purpose:

- Classify the ticket intent.

Input:

- Ticket text.

Output:

- Intent label.
- Confidence score.
- Reasoning summary.

Sensitivity:

- Safe.

#### `detect_priority`

Purpose:

- Detect urgency and business priority.

Input:

- Ticket text.
- Customer tier.
- Historical context.

Output:

- Priority level: `low`, `medium`, `high`, or `urgent`.
- Reason.

Sensitivity:

- Safe.

#### `extract_entities`

Purpose:

- Extract structured customer and ticket data.

Input:

- Ticket text.

Output:

- Customer name.
- Email address.
- Order ID.
- Product name.
- Issue type.
- Dates.

Sensitivity:

- Safe.

#### `search_knowledge_base`

Purpose:

- Retrieve relevant policy and support documentation.

Input:

- Query.
- Intent.
- Product.

Output:

- Matching documents.
- Source titles.
- Source snippets.
- Relevance scores.

Sensitivity:

- Safe.

#### `draft_email_response`

Purpose:

- Draft a customer-facing response.

Input:

- Ticket text.
- Extracted entities.
- Retrieved policies.
- Tone preference.

Output:

- Subject.
- Body.
- Policy references.
- Confidence score.

Sensitivity:

- Safe.

#### `send_email`

Purpose:

- Send the approved email to the customer.

Input:

- Recipient.
- Subject.
- Body.

Output:

- Email message ID.
- Delivery status.

Sensitivity:

- Approval required.

#### `create_crm_note`

Purpose:

- Create an internal note in the CRM.

Input:

- Customer ID.
- Note body.
- Related ticket ID.

Output:

- CRM note ID.
- Status.

Sensitivity:

- Approval required.

#### `summarize_tickets`

Purpose:

- Summarize a batch of tickets.

Input:

- Date range.
- Filters.

Output:

- Summary.
- Key themes.
- Top issue categories.
- Suggested actions.

Sensitivity:

- Safe.

#### `generate_report`

Purpose:

- Generate a support operations report.

Input:

- Ticket summaries.
- Metrics.
- Time period.

Output:

- Report title.
- Executive summary.
- Findings.
- Recommendations.

Sensitivity:

- Safe.

#### `export_report`

Purpose:

- Export or send a report externally.

Input:

- Report content.
- Destination.

Output:

- Export ID.
- Status.

Sensitivity:

- Approval required.

## 14. Suggested Data Model

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

## 15. API Design

### Ticket and Agent Run APIs

```text
POST /tickets
GET /tickets
GET /tickets/{ticket_id}

POST /agent-runs/support
POST /agent-runs/workflow
GET /agent-runs/{run_id}
GET /agent-runs/{run_id}/tool-calls
```

### Approval APIs

```text
GET /approvals
GET /approvals/{approval_id}
POST /approvals/{approval_id}/approve
POST /approvals/{approval_id}/reject
POST /approvals/{approval_id}/edit
POST /approvals/{approval_id}/execute
```

### Knowledge Base APIs

```text
POST /knowledge-documents
GET /knowledge-documents
POST /knowledge-documents/search
```

### Audit APIs

```text
GET /audit-logs
GET /audit-logs?agent_run_id={run_id}
GET /audit-logs?entity_type=approval_request
```

### Realtime APIs

```text
GET /ws/agent-runs/{run_id}
GET /ws/approvals
GET /ws/notifications
```

Realtime event types:

- `agent_run.started`
- `agent_run.step_started`
- `agent_run.step_completed`
- `tool_call.started`
- `tool_call.completed`
- `tool_call.failed`
- `approval.created`
- `approval.updated`
- `audit_log.created`
- `notification.created`

## 16. UI Requirements

The MVP dashboard should be simple and operations-focused.

### Frontend Design Standard

- Use taste-skill and tasteskill.dev as the quality reference for frontend polish.
- Adapt that taste to a serious B2B operations dashboard, not a landing page.
- The first screen should be the actual working product: ticket inbox, live agent status, and approval queue.
- Avoid generic AI SaaS visuals such as purple gradients, vague glass cards, oversized hero copy, and decorative mockups.
- Prioritize clarity, trust, speed, keyboard workflow, and readable operational density.

### Main Screens

#### Ticket Inbox

- List tickets by priority, status, and intent.
- Show AI classification.
- Open ticket detail.

#### Ticket Detail

- Original customer message.
- Extracted entities.
- Retrieved policy sources.
- Draft response.
- Recommended internal note.
- Proposed sensitive actions.

#### Approval Queue

- Pending actions.
- Tool name.
- Risk reason.
- Proposed payload.
- Approve, edit, or reject buttons.

#### Agent Run Timeline

- Step-by-step execution trace.
- Tool calls.
- Validation status.
- Retry attempts.
- Errors.
- Final output.

#### Audit Log

- Searchable event history.
- Actor.
- Event type.
- Entity.
- Timestamp.
- Before and after states.

## 17. Optimized Tech Stack

Technology choices reviewed on 2026-06-10.

### Architecture Summary

The recommended architecture is a production-style AI operations platform:

```text
React dashboard
-> FastAPI REST + WebSocket API
-> LangGraph agent workflows
-> Guardrail policy engine
-> Tool executor + approval service
-> PostgreSQL + pgvector
-> Redis Streams + Redis Pub/Sub
-> LLM gateway for hosted and local models
```

### Backend

- Python 3.12+.
- FastAPI for REST APIs and WebSocket endpoints.
- Pydantic v2 for request, response, tool input, and tool output validation.
- SQLAlchemy 2.x with async support.
- Alembic for database migrations.
- PostgreSQL 16+ or 17+ as the primary database.
- pgvector for vector storage and similarity search inside PostgreSQL.
- Redis for realtime events, background coordination, locks, rate limits, and short-lived state.
- ARQ, Dramatiq, or Celery for background workers.
- `structlog` or standard structured JSON logging.
- OpenTelemetry for traces and metrics.

Recommended MVP choice:

- Use `FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL + pgvector + Redis + ARQ`.

Why:

- FastAPI is excellent for Python async APIs, typed schemas, and WebSocket support.
- PostgreSQL keeps business data, audit logs, approvals, and knowledge documents in one reliable system.
- pgvector avoids adding a separate vector database too early.
- Redis gives the dashboard live agent-run updates and approval notifications.
- ARQ fits async Python well and keeps the MVP simpler than a full Celery deployment.

### Agent Orchestration

- Use LangGraph as the main workflow orchestration framework.
- Keep agent state explicit and serializable.
- Use LangGraph nodes for classification, extraction, retrieval, drafting, policy checks, approval interruption, tool execution, and final output.
- Use LangGraph interrupts for human approval checkpoints.
- Keep the policy engine outside the LLM.
- Keep tool execution deterministic and logged.
- Use LangSmith or OpenTelemetry tracing for debugging and evaluation.

Recommended LangGraph workflow:

```text
normalize_input
-> classify_intent
-> detect_priority
-> extract_entities
-> retrieve_policy_context
-> draft_response
-> plan_tool_actions
-> policy_gate
-> execute_safe_tools
-> create_approval_requests
-> wait_for_human_decision
-> execute_approved_tools
-> finalize_output
```

Why:

- LangGraph is designed for long-running, stateful, interruptible agent workflows.
- Human approval is a first-class workflow concern, not a UI-only feature.
- It gives better control than a simple autonomous agent loop.

### Realtime Layer

- Use FastAPI WebSockets for browser-to-backend realtime updates.
- Use Redis Pub/Sub for low-latency fanout to connected WebSocket clients.
- Use Redis Streams for durable internal events that workers can replay or acknowledge.
- Store important workflow state permanently in PostgreSQL.
- Use Redis only for realtime delivery, worker coordination, locks, rate limits, and ephemeral progress state.

Recommended event flow:

```text
LangGraph node emits event
-> event stored in PostgreSQL if audit-relevant
-> Redis Stream records durable event
-> Redis Pub/Sub broadcasts live update
-> FastAPI WebSocket manager sends update to React client
```

Use WebSockets for:

- Live agent run timeline.
- Tool call progress.
- Approval queue updates.
- Reviewer notifications.
- Background report generation progress.
- Execution failure alerts.

### LLM Provider Strategy

- Use a provider abstraction from day one.
- Use LiteLLM or a small internal adapter layer as the LLM gateway.
- Route hosted and local models through a common interface.
- Pin exact model IDs in configuration.
- Store model config in the database or environment-specific config files.
- Track provider, model name, token usage, latency, and cost for each agent run.

Recommended provider categories:

```text
Hosted frontier models:
- OpenAI GPT models.
- Anthropic Claude models.
- Google Gemini models.

Local and open-weight models:
- Ollama for local development.
- vLLM for production-grade local or private-cloud serving.
- llama.cpp for lightweight CPU/GPU edge deployment.
```

Recommended hosted model defaults:

- Primary free/default provider: Google Gemini Developer API.
- Default model: `gemini-3.1-flash-lite`.
- Optional stronger hosted model: `gemini-3.5-flash` if available in the project's free quota.
- Optional advanced model: `gemini-3.1-pro-preview` only for complex planning experiments or paid/preview testing.
- OpenAI and Anthropic adapters should remain supported by the architecture, but they are not the MVP default.

Why `gemini-3.1-flash-lite` is the MVP default:

- It is stable, low-latency, cost-efficient, and designed for high-frequency lightweight agentic tasks.
- It supports structured outputs, function calling, thinking, search grounding, URL context, and multimodal inputs.
- It fits this product's main workload: classification, entity extraction, summarization, policy-aware drafting, and routing.
- It works well as a model router that can decide whether a request should stay on Flash-Lite or escalate to a stronger model.

Gemini free-tier rule:

- Use Gemini free tier for demos, development, portfolio scenarios, and mock support data.
- Do not send real customer tickets containing PII to the free tier unless the data has been redacted and the data-use terms are acceptable.
- For real customer data, prefer local models, paid Gemini with proper data controls, or a private deployment.

Recommended local model defaults for this machine:

Detected machine:

```text
Acer Nitro AN515-58
CPU: Intel Core i5-12500H, 12 cores / 16 threads
RAM: 32GB
GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4GB VRAM
Runtime: Ollama installed
```

Current installed Ollama models:

```text
gemma3:4b
qwen3:8b
qwen2.5:7b
qwen2.5:3b
nomic-embed-text-v2-moe
```

Local model selection:

- Default local fallback: `gemma3:4b`.
- Best local quality mode currently installed: `qwen3:8b`.
- Fast local router/extractor currently installed: `qwen2.5:3b`.
- Local embedding model currently installed: `nomic-embed-text-v2-moe`.

Recommended next local pulls:

```text
ollama pull gemma3n:e4b
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
```

How to use them:

- `gemma3n:e4b`: best candidate for efficient local fallback on this laptop because it is designed for everyday devices and uses selective parameter activation.
- `qwen3.5:4b`: benchmark candidate for newer local reasoning, tool-use, and multilingual support workflows.
- `qwen3:8b`: use for higher-quality local reasoning when latency is acceptable; it is 5.2GB quantized, so it may partially offload to CPU because the RTX 3050 has 4GB VRAM.
- `gemma3:4b`: keep as the stable local default because it is already installed, smaller, multimodal, and fits the machine better.
- `qwen3-embedding:0.6b`: use as the preferred local embedding model for multilingual retrieval if it performs well in tests.

Serving recommendation for this machine:

- Use Ollama for local inference during MVP development.
- Do not use vLLM as the default on this laptop because 4GB VRAM is tight for production-style serving.
- Keep vLLM in the architecture for a future GPU server or cloud GPU deployment.

Models to avoid on this machine for the MVP:

- Avoid 12B, 14B, 20B, 27B, 30B, and larger local models as defaults.
- They may run through CPU/RAM offload, but the experience will be slow and not ideal for a realtime approval dashboard.
- Keep those models for future desktop/server GPU deployments, not the laptop MVP.

Practical model routing:

```text
classification/extraction:
  primary: gemini-3.1-flash-lite
  local fallback: gemma3:4b or qwen2.5:3b

policy retrieval query rewriting:
  primary: gemini-3.1-flash-lite
  local fallback: gemma3:4b

draft response:
  primary: gemini-3.1-flash-lite
  optional hosted escalation: gemini-3.5-flash if free quota allows
  local quality fallback: qwen3:8b

approval risk analysis:
  primary: gemini-3.1-flash-lite with higher thinking level
  local quality fallback: qwen3:8b

final customer-facing message:
  primary: gemini-3.1-flash-lite
  optional hosted escalation: gemini-3.5-flash if free quota allows
  local private fallback: gemma3:4b or qwen3:8b

report generation:
  primary: gemini-3.1-flash-lite
  local fallback: qwen3:8b
```

Recommended MVP model configuration:

```text
LLM_PRIMARY_PROVIDER=gemini
LLM_PRIMARY_MODEL=gemini-3.1-flash-lite
LLM_ESCALATION_MODEL=gemini-3.5-flash
LLM_ADVANCED_EXPERIMENT_MODEL=gemini-3.1-pro-preview

LOCAL_PROVIDER=ollama
LOCAL_FAST_MODEL=gemma3:4b
LOCAL_QUALITY_MODEL=qwen3:8b
LOCAL_ROUTER_MODEL=qwen2.5:3b
LOCAL_NEXT_FAST_MODEL=gemma3n:e4b
LOCAL_NEXT_BENCHMARK_MODEL=qwen3.5:4b

EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text-v2-moe
LOCAL_NEXT_EMBEDDING_MODEL=qwen3-embedding:0.6b
```

Important:

- Do not rely on the LLM to enforce business rules.
- The LLM may propose actions.
- The application policy engine decides whether actions are safe, approval-required, or blocked.
- Local models should be optional and configurable, not hard-coded into the workflow.

### Retrieval

Use PostgreSQL + pgvector as the default retrieval stack.

Recommended MVP retrieval architecture:

```text
knowledge_documents
-> markdown/html-aware chunking
-> local or hosted embeddings
-> PostgreSQL full-text index
-> pgvector HNSW index
-> hybrid retrieval
-> reranker
-> context packer with source citations
```

Recommended retrieval components:

- PostgreSQL full-text search with `tsvector` for keyword and policy-term matching.
- pgvector with HNSW indexes for semantic similarity search.
- Reciprocal Rank Fusion for hybrid ranking between keyword and vector results.
- Metadata filters for product, policy type, region, customer tier, and effective date.
- Reranking with a local reranker such as `bge-reranker-v2-m3` or a hosted reranker if allowed.
- Local embeddings with `qwen3-embedding:0.6b`, `nomic-embed-text-v2-moe`, BGE-M3, or Jina embeddings for private deployments.
- Hosted embeddings with Gemini Embedding when Gemini free quota or paid Gemini is acceptable.

Recommended default:

- Use `qwen3-embedding:0.6b` as the preferred local embedding candidate for multilingual retrieval after benchmarking.
- Use the already installed `nomic-embed-text-v2-moe` as the immediate local embedding fallback.
- Use Gemini Embedding when hosted embeddings are acceptable and quota allows.
- Store embeddings in `knowledge_chunks.embedding`.
- Add `content_tsvector` for keyword search.
- Rerank the top 20-50 candidates before sending context to the LLM.

Why this is the best fit:

- The knowledge base is policy-heavy, so exact policy terms matter.
- Vector-only search may miss order IDs, refund terms, product names, or policy codes.
- Keyword-only search may miss paraphrased customer issues.
- Hybrid retrieval gives better recall and better trust.
- PostgreSQL + pgvector keeps the MVP operationally simple.

When to add a separate vector database:

- Use Qdrant, Weaviate, or Milvus only if the knowledge base grows to millions of chunks, requires advanced vector filtering at high throughput, or must be operated independently from PostgreSQL.

### Frontend

Use option 2: FastAPI backend with a dedicated React frontend.

Recommended frontend stack:

- React 19+.
- TypeScript.
- Vite for a fast dashboard SPA.
- Tailwind CSS v4.
- Radix UI primitives or shadcn/ui for accessible, owned components.
- TanStack Query for server state.
- TanStack Router or React Router for routing.
- TanStack Table for ticket, approval, and audit tables.
- React Hook Form + Zod for forms and payload validation.
- Zustand for small UI state such as selected ticket, filters, and panel state.
- Motion for purposeful micro-interactions.
- Recharts, Tremor, or ECharts for operational charts.
- CodeMirror 6 or Monaco Editor for JSON payload review and editing.
- Playwright for end-to-end tests.
- Vitest + React Testing Library for component tests.

Design direction:

- Build a serious B2B operations dashboard, not a marketing landing page.
- Use taste-skill principles for visual quality: strong hierarchy, careful spacing, polished states, no generic AI-purple gradient UI.
- Use dense but readable layouts for support teams.
- Prioritize split-pane workflows: inbox on the left, ticket detail in the center, AI timeline and approval actions on the right.
- Make approval states visually obvious.
- Show policy sources and audit trail near the AI recommendation.
- Include empty, loading, error, streaming, retrying, approval-pending, approved, rejected, and failed states.
- Use keyboard-friendly workflows for reviewers.

Recommended primary screens:

- Ticket Inbox.
- Ticket Detail.
- Agent Run Timeline.
- Approval Queue.
- Approval Detail with payload diff.
- Knowledge Base Manager.
- Audit Log Explorer.
- Model and Tool Configuration.
- Settings for guardrail policies.

### Tool Execution and Background Jobs

- Use a `tool_executor` service that validates every input and output through Pydantic.
- Use background jobs for long-running summarization, report generation, retrieval indexing, and external API calls.
- Use Redis locks to prevent duplicate execution of approved sensitive actions.
- Retry only idempotent tools.
- Store every attempt in `tool_calls`.
- Use PostgreSQL transaction boundaries around approval status changes and execution records.

### Deployment

- Docker Compose.
- FastAPI API service.
- React web service.
- PostgreSQL with pgvector.
- Redis.
- Worker service.
- Optional Ollama service for local development.
- Optional vLLM service for local/private-cloud production inference.
- Environment-based provider keys.
- Nginx, Caddy, or Traefik as a reverse proxy.
- OpenTelemetry collector for traces and metrics.

Recommended MVP deployment:

```text
docker-compose.yml
  api
  web
  worker
  postgres
  redis
  ollama optional
```

Recommended production deployment:

- Containerized services on Kubernetes, Fly.io, Render, Railway, AWS ECS, or GCP Cloud Run.
- Managed PostgreSQL with pgvector support.
- Managed Redis.
- Separate worker replicas.
- Secrets stored in the cloud provider secret manager.
- Optional private GPU inference endpoint for vLLM.

## 18. Non-Functional Requirements

### Reliability

- Each tool must have a timeout.
- Retry only idempotent tools.
- Failed tool calls must be visible in the run timeline.
- Sensitive actions must not execute if approval status is invalid.
- WebSocket disconnects must not lose important state.
- Reconnect should reload the latest agent run state from PostgreSQL.
- Redis Streams should keep enough recent events for replay during short disconnects.

### Security

- Never store API keys in source code.
- Redact secrets from logs.
- Prevent the LLM from choosing unregistered tools.
- Prevent prompt injection from overriding approval rules.
- Do not allow users to edit audit history.
- Redact PII and secrets from LLM traces when needed.
- Restrict local model endpoints to private networks.
- Use signed approval actions or server-side permission checks.
- Block direct execution of approval-required tools from client-side requests.

### Observability

- Log every agent run.
- Log every tool call.
- Log every approval decision.
- Track token usage if supported by the selected LLM provider.
- Track latency per workflow step.
- Track WebSocket connection count and event delivery failures.
- Track retrieval hit rate, reranker score distribution, and source citation coverage.
- Track model, provider, cost, latency, and error rate per workflow step.

### Compliance Readiness

- Provide immutable-style audit records.
- Store reviewer identity for approval decisions.
- Store the final approved payload.
- Store the original AI-proposed payload.
- Store model name and retrieval sources used for each generated draft.
- Store approval state transitions as append-only audit events.

## 19. Example End-to-End Scenario

### Input Ticket

```text
Subject: Refund request for damaged product

Hi, I received my headphones today and the left side does not work.
I want a refund for order #12345.
```

### Agent Output

Intent:

```text
refund_request
```

Priority:

```text
high
```

Extracted entities:

```json
{
  "order_id": "12345",
  "product": "headphones",
  "issue_type": "damaged_or_defective_product"
}
```

Retrieved policy:

```text
Refunds for damaged products are eligible within 30 days of delivery.
Customers may be offered replacement or refund after verification.
```

Draft response:

```text
Subject: We can help with your order #12345

Hi,

I am sorry to hear that your headphones arrived with an issue. Based on our damaged product policy, your order may be eligible for a refund or replacement after verification.

Please confirm whether you would prefer a replacement or a refund, and our support team will help with the next step.

Best,
Support Team
```

Proposed sensitive action:

```json
{
  "tool_name": "send_email",
  "sensitivity": "approval_required",
  "risk_reason": "Customer-facing email must be reviewed before sending.",
  "payload": {
    "recipient": "customer@example.com",
    "subject": "We can help with your order #12345",
    "body": "..."
  }
}
```

Approval result:

```text
Human reviewer edits the response and approves sending.
```

Final action:

```text
Approved email is sent through the mock email adapter.
Audit log records the original draft, edited payload, reviewer, timestamp, and final delivery status.
```

## 20. Success Metrics

### Product Metrics

- Ticket classification accuracy.
- Entity extraction accuracy.
- Average response draft generation time.
- Percentage of drafts approved without edits.
- Average approval turnaround time.
- Number of sensitive actions blocked or queued correctly.
- Tool execution success rate.
- Tool retry rate.
- Audit log completeness.
- Realtime event delivery latency.
- Retrieval source citation coverage.
- Model cost per resolved ticket.
- Draft generation latency by model provider.

### Portfolio Metrics

- Clear demo flow.
- Strong README and architecture diagram.
- Test coverage for guardrails and approval logic.
- Realistic mock data.
- End-to-end scenario visible in UI.
- Clean API documentation.
- Working WebSocket demo for live agent-run progress.
- Local model demo profile through Ollama or vLLM.

## 21. Testing Strategy

### Unit Tests

- Classification response parser.
- Entity extraction schema validation.
- Tool registry validation.
- Guardrail policy decisions.
- Approval state transitions.
- Retry and timeout behavior.

### Integration Tests

- Full ticket-to-draft workflow.
- Sensitive action creates approval request.
- Approved action executes.
- Rejected action does not execute.
- Blocked action is denied.
- Tool call logs are written.

### Evaluation Tests

- Sample tickets with expected intent labels.
- Sample tickets with expected entities.
- Policy retrieval relevance tests.
- Hybrid retrieval and reranker regression tests.
- Draft response quality checklist.
- WebSocket event delivery tests.
- Model routing tests.

## 22. Implementation Roadmap

### Phase 1: Core Backend

- Define Pydantic schemas.
- Set up FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pgvector, and Redis.
- Build tool registry.
- Build guardrail policy engine.
- Build audit logging service.
- Build approval state machine.
- Build Redis event publisher for agent-run and approval events.
- Build background worker service.
- Create mock tools.

### Phase 2: Support Agent Workflow

- Implement LangGraph support workflow.
- Add ticket input.
- Add classification.
- Add priority detection.
- Add entity extraction.
- Add hybrid knowledge base retrieval with PostgreSQL full-text search and pgvector.
- Add reranking and source citation packing.
- Add draft response generation.
- Add support workflow orchestration.

### Phase 3: React Dashboard and Realtime UI

- Build React + TypeScript + Tailwind dashboard.
- Add WebSocket client for live agent-run updates.
- Build approval queue.
- Add approve, reject, and edit actions.
- Show proposed payload and risk reason.
- Execute approved mock actions.
- Show audit trail.
- Add payload diff viewer for edited approval actions.

### Phase 4: Workflow Automation Mode

- Add free-text instruction input.
- Convert instruction into a plan.
- Execute safe tools.
- Queue sensitive tools.
- Generate reports and summaries.

### Phase 5: Polish and Portfolio

- Add seed data.
- Add demo scripts.
- Add Docker Compose.
- Add local Ollama profile and optional vLLM profile.
- Add model provider configuration examples.
- Add architecture diagram.
- Add README.
- Add tests.
- Add screenshots or short demo video.

## 23. Suggested Repository Structure

```text
ai-agent-human-approval/
  app/
    main.py
    api/
      tickets.py
      agent_runs.py
      approvals.py
      audit_logs.py
      knowledge.py
      websocket.py
    core/
      config.py
      database.py
      redis.py
      security.py
      telemetry.py
    agents/
      support_agent.py
      workflow_agent.py
      planner.py
      state.py
    guardrails/
      policy_engine.py
      sensitivity.py
      prompt_injection.py
    llm/
      gateway.py
      providers.py
      model_router.py
    tools/
      registry.py
      schemas.py
      support_tools.py
      mock_email.py
      mock_crm.py
      mock_refund.py
    retrieval/
      chunking.py
      embeddings.py
      hybrid_search.py
      reranker.py
      context_packer.py
    models/
      ticket.py
      agent_run.py
      tool_call.py
      approval.py
      audit_log.py
      knowledge_document.py
      knowledge_chunk.py
      model_config.py
    services/
      audit_service.py
      approval_service.py
      tool_executor.py
      retrieval_service.py
      event_service.py
      websocket_manager.py
    workers/
      jobs.py
      worker.py
    tests/
      test_guardrails.py
      test_approvals.py
      test_tool_executor.py
      test_support_workflow.py
      test_retrieval.py
      test_websocket_events.py
  migrations/
    versions/
  frontend/
    src/
      app/
        router.tsx
        query-client.ts
      components/
        approvals/
        audit/
        tickets/
        timeline/
        ui/
      features/
        approval-queue/
        ticket-detail/
        agent-runs/
        knowledge-base/
        settings/
      lib/
        api.ts
        websocket.ts
        schemas.ts
      main.tsx
    package.json
    vite.config.ts
    tailwind.config.ts
  docs/
    architecture.md
    demo_scenarios.md
  docker-compose.yml
  docker-compose.local-llm.yml
  Dockerfile
  frontend.Dockerfile
  README.md
```

## 24. Portfolio Value

This project demonstrates practical AI engineering, not just prompt engineering.

It shows that the builder understands:

- Agent workflow design.
- Human-in-the-loop systems.
- LLM tool calling.
- Structured validation.
- Guardrails.
- Auditability.
- Backend API design.
- Workflow orchestration.
- Product thinking.
- Real business risk.

## 25. Best MVP Demo Script

1. Open the dashboard.
2. Submit a refund ticket.
3. Show extracted entities and classification.
4. Show retrieved policy document.
5. Show AI-generated draft response.
6. Show that `send_email` is not executed automatically.
7. Open the approval queue.
8. Edit and approve the email.
9. Execute the approved mock email action.
10. Open the audit log and show every step.
11. Run a workflow instruction to summarize last week's tickets.
12. Show report generation and approval before export.

## 26. Final Optimized Version

The best version of this idea is:

> A human-in-the-loop AI support operations platform that automates ticket understanding, policy retrieval, response drafting, and workflow preparation while enforcing code-level guardrails and requiring human approval for sensitive actions.

This version is more focused, easier to build, easier to demo, and more compelling for AI engineer, backend engineer, and automation engineer opportunities.
