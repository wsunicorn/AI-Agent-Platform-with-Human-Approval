# Project Checklist

Use this as the main progress tracker.

Status legend:

- `[ ]` Not started
- `[x]` Done

## Phase 0: Project Planning

- [x] Write project idea.
- [x] Choose optimized architecture.
- [x] Choose Gemini-free-first LLM strategy.
- [x] Choose local model strategy for the target machine.
- [x] Create project docs folder.
- [x] Create implementation checklist.
- [x] Create initial README.
- [x] Create architecture diagram image.
- [x] Create project board or issue list.

## Phase 1: Repository Setup

- [x] Initialize Git repository.
- [x] Create backend folder structure.
- [x] Create frontend folder structure.
- [x] Add `.gitignore`.
- [x] Add `.env.example`.
- [x] Add `docker-compose.yml`.
- [x] Add `docker-compose.local-llm.yml`.
- [x] Add backend dependency file.
- [x] Add frontend package setup.
- [x] Add formatting and linting setup.

## Phase 2: Infrastructure

- [x] Add PostgreSQL service.
- [x] Add Redis service.
- [x] Add optional Ollama service profile.
- [x] Verify PostgreSQL connection.
- [x] Verify Redis connection.
- [x] Add FastAPI health endpoint.
- [x] Add worker health check.
- [x] Add frontend health/status page.

## Phase 3: Database and Models

- [x] Configure SQLAlchemy async engine.
- [x] Configure Alembic.
- [x] Create `tickets` table.
- [x] Create `agent_runs` table.
- [x] Create `tool_calls` table.
- [x] Create `approval_requests` table.
- [x] Create `audit_logs` table.
- [x] Create `knowledge_documents` table.
- [x] Create `knowledge_chunks` table.
- [x] Create `model_configs` table.
- [x] Add pgvector extension migration.
- [x] Add full-text search indexes.
- [x] Add vector HNSW index.
- [x] Add seed data.

## Phase 4: Core Backend Services

- [x] Implement config loader.
- [x] Implement database session dependency.
- [x] Implement Redis client.
- [x] Implement audit service.
- [x] Implement event service.
- [x] Implement WebSocket manager.
- [x] Implement approval service.
- [x] Implement tool registry.
- [x] Implement tool executor.
- [x] Implement retry and timeout policy.
- [x] Implement Redis lock for sensitive action execution.

## Phase 5: Guardrails and Approval Logic

- [x] Define sensitivity enum.
- [x] Define safe tools.
- [x] Define approval-required tools.
- [x] Define blocked tools.
- [x] Implement policy engine.
- [x] Block unregistered tools.
- [x] Block invalid tool payloads.
- [x] Block direct sensitive action execution.
- [x] Create approval request from approval-required action.
- [x] Support approve.
- [x] Support reject.
- [x] Support edit and approve.
- [x] Support execute approved action.
- [x] Prevent duplicate execution.
- [x] Log all approval state transitions.

## Phase 6: Mock Tools

- [x] Implement `classify_ticket`.
- [x] Implement `detect_priority`.
- [x] Implement `extract_entities`.
- [x] Implement `search_knowledge_base`.
- [x] Implement `draft_email_response`.
- [x] Implement `send_email` mock.
- [x] Implement `create_crm_note` mock.
- [x] Implement `summarize_tickets`.
- [x] Implement `generate_report`.
- [x] Implement `export_report` mock.
- [x] Validate every tool input with Pydantic.
- [x] Validate every tool output with Pydantic.
- [x] Log every tool call.

## Phase 7: LLM Gateway

- [x] Create provider interface.
- [x] Implement Gemini provider.
- [x] Implement Ollama provider.
- [x] Add model routing config.
- [x] Add `gemini-3.1-flash-lite` default.
- [x] Add local fallback `gemma3:4b`.
- [x] Add quality fallback `qwen3:8b`.
- [x] Add fast router `qwen2.5:3b`.
- [x] Add token/latency tracking.
- [x] Add provider error handling.
- [x] Add fallback behavior.
- [x] Add PII redaction hook before hosted calls.

## Phase 8: Retrieval

- [x] Implement document ingestion.
- [x] Implement chunking.
- [x] Implement embedding generation.
- [x] Store chunks and embeddings.
- [x] Implement PostgreSQL full-text search.
- [x] Implement pgvector semantic search.
- [x] Implement hybrid fusion.
- [x] Implement metadata filters.
- [x] Implement reranking.
- [x] Implement context packing with citations.
- [x] Add retrieval evaluation examples.
- [x] Add knowledge base search API.

## Phase 9: LangGraph Workflows

- [x] Define support agent state.
- [x] Define workflow automation state.
- [x] Implement `normalize_input`.
- [x] Implement `classify_intent`.
- [x] Implement `detect_priority`.
- [x] Implement `extract_entities`.
- [x] Implement `retrieve_policy_context`.
- [x] Implement `draft_response`.
- [x] Implement `plan_tool_actions`.
- [x] Implement `policy_gate`.
- [x] Implement `execute_safe_tools`.
- [x] Implement `create_approval_requests`.
- [x] Implement human approval pause.
- [x] Implement `execute_approved_tools`.
- [x] Implement `finalize_output`.
- [x] Emit events for every node.
- [x] Persist workflow state.

## Phase 10: REST and WebSocket APIs

- [x] Implement ticket APIs.
- [x] Implement support agent run API.
- [x] Implement workflow agent run API.
- [x] Implement tool call list API.
- [x] Implement approval APIs.
- [x] Implement knowledge base APIs.
- [x] Implement audit log APIs.
- [x] Implement model config APIs.
- [x] Implement tool config APIs.
- [x] Implement WebSocket agent run endpoint.
- [x] Implement WebSocket approvals endpoint.
- [x] Implement WebSocket notifications endpoint.
- [x] Add reconnect behavior.

## Phase 11: Frontend Foundation

- [x] Create Vite React app.
- [x] Configure TypeScript.
- [x] Configure Tailwind CSS v4.
- [x] Add routing.
- [x] Add TanStack Query.
- [x] Add API client.
- [x] Add WebSocket client.
- [x] Add base layout.
- [x] Add sidebar navigation.
- [x] Add top status bar.
- [x] Add shared UI components.
- [x] Add empty/loading/error states.

## Phase 12: Frontend Screens

- [x] Build Ticket Inbox.
- [x] Build Ticket Detail.
- [x] Build Agent Run Timeline.
- [x] Build Approval Queue.
- [x] Build Approval Detail.
- [x] Build editable payload view.
- [x] Build payload diff view.
- [x] Build Knowledge Base Manager.
- [x] Build Audit Log Explorer.
- [x] Build Model Settings.
- [x] Build Tool Settings.
- [x] Build Guardrail Settings.
- [x] Add live WebSocket updates to timeline.
- [x] Add live approval notifications.

## Phase 13: Testing

- [x] Unit test policy engine.
- [x] Unit test approval state machine.
- [x] Unit test tool executor.
- [x] Unit test retry and timeout logic.
- [x] Unit test LLM routing.
- [x] Unit test retrieval fusion.
- [x] Integration test support ticket workflow.
- [x] Integration test sensitive action approval.
- [x] Integration test rejected action.
- [x] Integration test blocked action.
- [x] Integration test audit logging.
- [x] WebSocket event delivery test.
- [x] Frontend component tests.
- [x] Playwright refund-ticket demo test.
- [x] Playwright approval edit-and-execute test.


## Phase 14: Demo and Portfolio Polish

- [x] Add demo support tickets.
- [x] Add demo policy documents.
- [x] Add demo CRM data.
- [x] Add demo report data.
- [x] Write README quickstart.
- [x] Add screenshots.
- [x] Add short demo video script.
- [x] Add architecture diagram.
- [x] Add API examples.
- [x] Add final case study summary.

## Phase 15: Final Acceptance

- [x] Refund ticket demo works end-to-end.
- [x] Blocked delete request is denied.
- [x] Weekly report demo works.
- [x] CRM note approval works.
- [x] Audit log records every tool and approval action.
- [x] Dashboard updates live through WebSockets.
- [x] Local model fallback works.
- [x] Gemini default route works.
- [x] Docker Compose starts all required services.
- [x] Tests pass.
- [x] README explains how to run the project.

