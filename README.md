# AI Agent Platform with Human Approval

Human-in-the-loop AI support operations platform with ticket classification, tool calling, guardrails, audit logs, realtime updates, and approval workflows for sensitive actions.

## Current Status

Planning, documentation, repository setup, and local infrastructure skeleton are in progress.

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

