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

- [ ] Configure SQLAlchemy async engine.
- [ ] Configure Alembic.
- [ ] Create `tickets` table.
- [ ] Create `agent_runs` table.
- [ ] Create `tool_calls` table.
- [ ] Create `approval_requests` table.
- [ ] Create `audit_logs` table.
- [ ] Create `knowledge_documents` table.
- [ ] Create `knowledge_chunks` table.
- [ ] Create `model_configs` table.
- [ ] Add pgvector extension migration.
- [ ] Add full-text search indexes.
- [ ] Add vector HNSW index.
- [ ] Add seed data.

## Phase 4: Core Backend Services

- [ ] Implement config loader.
- [ ] Implement database session dependency.
- [ ] Implement Redis client.
- [ ] Implement audit service.
- [ ] Implement event service.
- [ ] Implement WebSocket manager.
- [ ] Implement approval service.
- [ ] Implement tool registry.
- [ ] Implement tool executor.
- [ ] Implement retry and timeout policy.
- [ ] Implement Redis lock for sensitive action execution.

## Phase 5: Guardrails and Approval Logic

- [ ] Define sensitivity enum.
- [ ] Define safe tools.
- [ ] Define approval-required tools.
- [ ] Define blocked tools.
- [ ] Implement policy engine.
- [ ] Block unregistered tools.
- [ ] Block invalid tool payloads.
- [ ] Block direct sensitive action execution.
- [ ] Create approval request from approval-required action.
- [ ] Support approve.
- [ ] Support reject.
- [ ] Support edit and approve.
- [ ] Support execute approved action.
- [ ] Prevent duplicate execution.
- [ ] Log all approval state transitions.

## Phase 6: Mock Tools

- [ ] Implement `classify_ticket`.
- [ ] Implement `detect_priority`.
- [ ] Implement `extract_entities`.
- [ ] Implement `search_knowledge_base`.
- [ ] Implement `draft_email_response`.
- [ ] Implement `send_email` mock.
- [ ] Implement `create_crm_note` mock.
- [ ] Implement `summarize_tickets`.
- [ ] Implement `generate_report`.
- [ ] Implement `export_report` mock.
- [ ] Validate every tool input with Pydantic.
- [ ] Validate every tool output with Pydantic.
- [ ] Log every tool call.

## Phase 7: LLM Gateway

- [ ] Create provider interface.
- [ ] Implement Gemini provider.
- [ ] Implement Ollama provider.
- [ ] Add model routing config.
- [ ] Add `gemini-3.1-flash-lite` default.
- [ ] Add local fallback `gemma3:4b`.
- [ ] Add quality fallback `qwen3:8b`.
- [ ] Add fast router `qwen2.5:3b`.
- [ ] Add token/latency tracking.
- [ ] Add provider error handling.
- [ ] Add fallback behavior.
- [ ] Add PII redaction hook before hosted calls.

## Phase 8: Retrieval

- [ ] Implement document ingestion.
- [ ] Implement chunking.
- [ ] Implement embedding generation.
- [ ] Store chunks and embeddings.
- [ ] Implement PostgreSQL full-text search.
- [ ] Implement pgvector semantic search.
- [ ] Implement hybrid fusion.
- [ ] Implement metadata filters.
- [ ] Implement reranking.
- [ ] Implement context packing with citations.
- [ ] Add retrieval evaluation examples.
- [ ] Add knowledge base search API.

## Phase 9: LangGraph Workflows

- [ ] Define support agent state.
- [ ] Define workflow automation state.
- [ ] Implement `normalize_input`.
- [ ] Implement `classify_intent`.
- [ ] Implement `detect_priority`.
- [ ] Implement `extract_entities`.
- [ ] Implement `retrieve_policy_context`.
- [ ] Implement `draft_response`.
- [ ] Implement `plan_tool_actions`.
- [ ] Implement `policy_gate`.
- [ ] Implement `execute_safe_tools`.
- [ ] Implement `create_approval_requests`.
- [ ] Implement human approval pause.
- [ ] Implement `execute_approved_tools`.
- [ ] Implement `finalize_output`.
- [ ] Emit events for every node.
- [ ] Persist workflow state.

## Phase 10: REST and WebSocket APIs

- [ ] Implement ticket APIs.
- [ ] Implement support agent run API.
- [ ] Implement workflow agent run API.
- [ ] Implement tool call list API.
- [ ] Implement approval APIs.
- [ ] Implement knowledge base APIs.
- [ ] Implement audit log APIs.
- [ ] Implement model config APIs.
- [ ] Implement tool config APIs.
- [ ] Implement WebSocket agent run endpoint.
- [ ] Implement WebSocket approvals endpoint.
- [ ] Implement WebSocket notifications endpoint.
- [ ] Add reconnect behavior.

## Phase 11: Frontend Foundation

- [ ] Create Vite React app.
- [ ] Configure TypeScript.
- [ ] Configure Tailwind CSS v4.
- [ ] Add routing.
- [ ] Add TanStack Query.
- [ ] Add API client.
- [ ] Add WebSocket client.
- [ ] Add base layout.
- [ ] Add sidebar navigation.
- [ ] Add top status bar.
- [ ] Add shared UI components.
- [ ] Add empty/loading/error states.

## Phase 12: Frontend Screens

- [ ] Build Ticket Inbox.
- [ ] Build Ticket Detail.
- [ ] Build Agent Run Timeline.
- [ ] Build Approval Queue.
- [ ] Build Approval Detail.
- [ ] Build editable payload view.
- [ ] Build payload diff view.
- [ ] Build Knowledge Base Manager.
- [ ] Build Audit Log Explorer.
- [ ] Build Model Settings.
- [ ] Build Tool Settings.
- [ ] Build Guardrail Settings.
- [ ] Add live WebSocket updates to timeline.
- [ ] Add live approval notifications.

## Phase 13: Testing

- [ ] Unit test policy engine.
- [ ] Unit test approval state machine.
- [ ] Unit test tool executor.
- [ ] Unit test retry and timeout logic.
- [ ] Unit test LLM routing.
- [ ] Unit test retrieval fusion.
- [ ] Integration test support ticket workflow.
- [ ] Integration test sensitive action approval.
- [ ] Integration test rejected action.
- [ ] Integration test blocked action.
- [ ] Integration test audit logging.
- [ ] WebSocket event delivery test.
- [ ] Frontend component tests.
- [ ] Playwright refund-ticket demo test.
- [ ] Playwright approval edit-and-execute test.

## Phase 14: Demo and Portfolio Polish

- [ ] Add demo support tickets.
- [ ] Add demo policy documents.
- [ ] Add demo CRM data.
- [ ] Add demo report data.
- [ ] Write README quickstart.
- [ ] Add screenshots.
- [ ] Add short demo video script.
- [ ] Add architecture diagram.
- [ ] Add API examples.
- [ ] Add final case study summary.

## Phase 15: Final Acceptance

- [ ] Refund ticket demo works end-to-end.
- [ ] Blocked delete request is denied.
- [ ] Weekly report demo works.
- [ ] CRM note approval works.
- [ ] Audit log records every tool and approval action.
- [ ] Dashboard updates live through WebSockets.
- [ ] Local model fallback works.
- [ ] Gemini default route works.
- [ ] Docker Compose starts all required services.
- [ ] Tests pass.
- [ ] README explains how to run the project.
