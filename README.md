# AI Agent Platform with Human Approval

Human-in-the-loop AI support operations platform with ticket classification, tool calling, guardrails, audit logs, realtime updates, and approval workflows for sensitive actions.

## Current Status

All phases (Phases 0-15) are fully implemented and verified, including planning, infrastructure, database models, core backend services, guardrails, approval logic, mock tools, LLM gateway, hybrid RAG retrieval, LangGraph workflow execution, REST/WebSocket APIs, the React dashboard webapp, and comprehensive unit, integration, and Playwright E2E tests.

## Tech Stack

- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, pgvector, Redis.
- Agent workflow: LangGraph.
- Realtime: FastAPI WebSockets, Redis Pub/Sub, Redis Streams.
- LLM: Gemini free-first with Ollama local fallback.
- Frontend: React, TypeScript, Vite, Tailwind CSS v4.

## Documentation

- [Documentation index](docs/README.md)
- [Project checklist](docs/PROJECT_CHECKLIST.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Tech stack](docs/TECH_STACK.md)
- [LLM and retrieval](docs/LLM_AND_RETRIEVAL.md)
- [Mock tools](docs/MOCK_TOOLS.md)

## Quickstart

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Start the core infrastructure:

```powershell
docker compose up -d postgres redis
```

Start all local services:

```powershell
docker compose up --build
```

Run database migrations and seed demo data:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Phase 4 core services now include audit logging, Redis events, topic-based WebSocket
connection management, approval state transitions, tool registry/execution, retry
timeouts, and Redis locks for sensitive action execution.

Phase 5 guardrails now enforce safe, approval-required, and blocked tool policies
before execution. Sensitive tools require approval and duplicate approved execution is
blocked.

Phase 6 mock tools now cover ticket classification, priority detection, entity
extraction, knowledge search, email drafting, ticket summarization, report
generation, mock email sending, mock CRM notes, and mock report export.

API health:

```text
http://localhost:8000/health/live
http://localhost:8000/health/ready
```

Frontend:

```text
http://localhost:5173
```

Optional local LLM profile:

```powershell
docker compose -f docker-compose.yml -f docker-compose.local-llm.yml --profile local-llm up -d ollama
```

## GitHub

Repository target:

```text
https://github.com/wsunicorn/AI-Agent-Platform-with-Human-Approval.git
```
