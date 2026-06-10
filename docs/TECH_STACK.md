# Tech Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL 16+ or 17+
- pgvector
- Redis
- ARQ for async background jobs
- LangGraph
- LiteLLM or an internal LLM gateway
- OpenTelemetry
- `structlog` or JSON structured logging

## Frontend

- React 19+
- TypeScript
- Vite
- Tailwind CSS v4
- Radix UI primitives or shadcn/ui
- TanStack Query
- TanStack Router or React Router
- TanStack Table
- React Hook Form
- Zod
- Zustand
- Motion
- CodeMirror 6 or Monaco Editor for JSON payload review
- Playwright
- Vitest
- React Testing Library

## Realtime

- FastAPI WebSockets for browser connections.
- Redis Pub/Sub for low-latency fanout.
- Redis Streams for durable internal workflow events.

## LLM Defaults

Primary hosted/free provider:

- Google Gemini Developer API

Default hosted model:

- `gemini-3.1-flash-lite`

Optional stronger hosted model:

- `gemini-3.5-flash`

Advanced experiment model:

- `gemini-3.1-pro-preview`

Local runtime:

- Ollama

Current local models on the target machine:

- `gemma3:4b`
- `qwen3:8b`
- `qwen2.5:7b`
- `qwen2.5:3b`
- `nomic-embed-text-v2-moe`

Recommended next local pulls:

```text
ollama pull gemma3n:e4b
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
```

## Retrieval Stack

- PostgreSQL full-text search with `tsvector`.
- pgvector HNSW index for semantic search.
- Hybrid retrieval with Reciprocal Rank Fusion.
- Metadata filters.
- Reranker before context packing.
- Local embeddings by default.

Preferred embedding order:

1. `qwen3-embedding:0.6b` after benchmarking.
2. `nomic-embed-text-v2-moe` as the installed immediate fallback.
3. Gemini Embedding when hosted embeddings are acceptable.

## Deployment

MVP:

- Docker Compose
- `api`
- `worker`
- `web`
- `postgres`
- `redis`
- optional `ollama`

Future production:

- Managed PostgreSQL with pgvector.
- Managed Redis.
- Container runtime such as ECS, Cloud Run, Fly.io, Render, Railway, or Kubernetes.
- Optional private GPU endpoint for vLLM.

