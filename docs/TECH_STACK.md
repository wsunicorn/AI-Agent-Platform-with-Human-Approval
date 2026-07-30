# Tech Stack

This lists what's actually pinned in `requirements.txt` / `frontend/package.json`
and actually used in the code, not the original candidate list.

## Backend (`requirements.txt`)

- Python 3.12+ (`pyproject.toml` targets `py312`)
- FastAPI 0.124, Uvicorn (standard extras)
- Pydantic v2.12 + pydantic-settings 2.12
- SQLAlchemy 2.0 async + asyncpg
- Alembic 1.17
- PostgreSQL 16 (built with pgvector baked in via `postgres.Dockerfile`) + `pgvector` 0.4 Python bindings
- Redis 5.3 (`redis.asyncio` client)
- `arq` 0.26 — installed, but **not wired to anything**; there is no job
  queue, worker pool, or scheduled task defined anywhere in `app/`. The
  `worker` container just runs a heartbeat loop (`app/workers/worker.py`).
- LangGraph 1.0
- LiteLLM 1.80 — both `app/llm/gemini.py` and `app/llm/ollama.py` call
  `litellm.acompletion` / `litellm.aembedding` rather than each provider's
  native SDK.
- structlog 25.5 for structured logging
- OpenTelemetry API/SDK 1.39 — installed, but nothing in `app/` currently
  initializes a tracer or exporter; there is no active tracing today.

## Frontend (`frontend/package.json`)

- React 19, TypeScript ~5.9, Vite 7
- Tailwind CSS v4 (via `@tailwindcss/vite`)
- `@radix-ui/themes` (the higher-level themed component package) plus
  individual primitives: `@radix-ui/react-dialog`, `-dropdown-menu`, `-tabs`.
  Not shadcn/ui.
- TanStack Query v5 (data fetching/caching) — **actually used**.
- `@tanstack/react-router` and `@tanstack/react-table` are listed as
  dependencies but **not imported anywhere in `frontend/src`.** There is no
  client-side router: `frontend/src/app/App.tsx` switches views with plain
  `useState`, so the app has no deep-linkable URLs. See
  [`FRONTEND_SPEC.md`](FRONTEND_SPEC.md).
- React Hook Form 7 + `@hookform/resolvers` + Zod 4 — present as
  dependencies; forms in the current pages (ticket creation, document
  creation) are plain controlled `useState` inputs, not wired through
  `react-hook-form`/Zod schemas yet.
- Zustand 5 — present, not currently used for any store (no `create()` calls
  in `frontend/src`); all state is local component state + TanStack Query cache.
- Motion (Framer Motion successor) — present, not currently used for any
  animation in the shipped pages.
- `@uiw/react-codemirror` — used for the approval payload JSON editor
  (`ApprovalDetail.tsx`).
- `@phosphor-icons/react` — the icon set actually used throughout every page.
- `recharts` — installed; no chart is currently rendered anywhere in
  `frontend/src`.
- Playwright + Vitest + React Testing Library — used for the two E2E specs
  and two component test files that exist today (see
  [`DEVELOPMENT_SETUP.md`](DEVELOPMENT_SETUP.md) for how to run them).

Several of these dependencies (router, table, react-hook-form/zod, zustand,
motion, recharts) are installed and ready but not yet wired into any page —
treat them as "available for the next feature", not "in active use".

## Realtime

- FastAPI native WebSockets for browser connections (`app/api/websockets.py`).
- Redis Pub/Sub for fanout from the API process's event publisher to any
  connected WebSocket clients (same process re-broadcasts; there's currently
  only ever one `api` replica in `docker-compose.yml`, so Pub/Sub isn't yet
  doing cross-process fanout, just decoupling publish from broadcast).
- Redis Streams for durable event history — written on every publish, but
  nothing currently reads a stream back (no replay/backfill feature yet).

## LLM

Primary hosted provider: Google Gemini, called through LiteLLM
(`app/llm/gemini.py`). Default model `gemini-3.1-flash-lite`; a `quality`
routing purpose additionally tries `gemini-3.5-flash` first
(`app/llm/router.py:_DEFAULT_ROUTING`) — this escalation model is a hardcoded
routing-table entry, not something read from configuration.

Local runtime: Ollama, also called through LiteLLM (`app/llm/ollama.py`).
Fallback chains per task purpose (classification/extraction/drafting/
routing/quality/embedding/reranking) are defined in
`app/llm/router.py` — see [`LLM_AND_RETRIEVAL.md`](LLM_AND_RETRIEVAL.md) for
the full table and which environment variables actually affect them.

## Retrieval Stack

- PostgreSQL full-text search via a generated `tsvector` column (`simple`
  config at query time, `english` config at storage time — see
  [`DATA_MODEL.md`](DATA_MODEL.md)).
- pgvector HNSW index (`vector_cosine_ops`) for semantic search, 768-dim
  embeddings.
- Hybrid retrieval via Reciprocal Rank Fusion (`app/retrieval/search.py`),
  falling back to full-text-only results if the vector search returns
  nothing or errors.
- LLM-based reranking (`app/retrieval/reranker.py`) — only actually invoked
  when the candidate set exceeds `top_k`; otherwise it's a no-op passthrough.
- Local embeddings by default (`nomic-embed-text-v2-moe` via Ollama).

## Deployment

`docker-compose.yml` defines five services: `postgres`, `redis`, `api`,
`worker`, `web`. There is no separate reverse proxy, no TLS termination, and
no auth layer in this compose file — it's a local/demo topology, not a
production one. An optional `ollama` profile is added by
`docker-compose.local-llm.yml` (see the root `README.md` for the exact command).
