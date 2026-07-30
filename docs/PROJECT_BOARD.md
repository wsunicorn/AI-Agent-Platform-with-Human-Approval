# Project Board

Lightweight local project board until GitHub Issues/Projects are set up.
Last reconciled against the actual codebase on 2026-07-30 — see
[`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) for the full phase-by-phase
history (Phases 0-15 are implemented and tested).

## Done

All of Phases 0-15: planning docs, repo/infra setup, database + models,
core backend services, guardrails/approvals, mock tools, LLM gateway,
hybrid retrieval, LangGraph workflows, REST/WebSocket APIs, React dashboard,
unit/integration/E2E tests, demo polish.

## Known gaps and real next-step candidates

These were found during a full code/doc audit. None of them break the demo
happy path, but they're the honest list of what's incomplete or half-wired,
in rough priority order:

1. **No auth/reviewer identity.** Every approval action is attributed to a
   hardcoded `"admin"` string from the frontend. Needed before this could be
   a multi-reviewer tool.
2. **Model Configs Settings screen is cosmetic.** `/settings/model-configs`
   reads/writes the `model_configs` table, but `app/llm/router.py` doesn't
   consult it — routing is a hardcoded table. Either wire the router to read
   `ModelConfig` rows, or relabel the screen as informational.
3. **Approval realtime is unwired on the frontend.** `/ws/approvals` and
   `/ws/notifications` work on the backend; `ApprovalQueue`/`ApprovalDetail`
   only poll every 5s. `createApprovalSocket`/`createNotificationSocket`
   already exist in `frontend/src/lib/websocket.ts` and just need to be
   plugged into those two pages.
4. **No client-side router.** Navigation is in-memory `useState`; no deep
   links, no back/forward, reload always returns to the ticket inbox.
   `@tanstack/react-router` is already a dependency.
5. **`execute_approved_tools` is dead code in both LangGraph graphs.**
   Approval execution actually happens via a direct `ToolExecutor.execute_approved`
   call from the REST layer, not by resuming the graph. Either remove the
   unreachable node/edges, or invest in a real checkpointer-based resume if
   you want the graph to be the single source of truth for execution.
6. **No "cancel approval" action.** `ApprovalStatus.CANCELLED` exists in the
   enum; nothing sets it.
7. **`arq` is an unused dependency.** The `worker` container is a heartbeat
   stub. If workflow execution or ingestion needs to move off the API
   process, this is where a real job queue would go.
8. **Guardrail catalog overrides aren't persisted.** `/settings/tools` and
   `/settings/guardrail-policies` edits are in-memory (process-global) and
   reset on restart.
9. **Workflow Automation mode has no retrieval step**, unlike the Support
   Agent flow — instructions are planned from the LLM's own knowledge only.

## Issue Templates

### Feature

```text
Title:
Context:
Acceptance criteria:
Test notes:
Docs impact:
```

### Bug

```text
Title:
Observed behavior:
Expected behavior:
Reproduction steps:
Environment:
```

### Tech Debt

```text
Title:
Why it matters:
Proposed change:
Risk:
```
