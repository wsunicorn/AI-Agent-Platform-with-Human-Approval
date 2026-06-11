# Development Setup

## Prerequisites

- Python 3.12+
- Node.js 22+
- Docker Desktop
- PostgreSQL client tools
- Redis CLI optional
- Ollama

## Local Services

Docker Compose should run:

- `postgres`
- `redis`
- `api`
- `worker`
- `web`
- optional `ollama`

PostgreSQL is built from `postgres.Dockerfile` so the local database includes pgvector
without depending on the external `pgvector/pgvector` image.

## Backend Setup Plan

```text
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -r requirements-dev.txt
```

Dependencies are pinned in `requirements.txt` and `requirements-dev.txt`.

## Database Migrations

```powershell
docker compose up -d --build postgres redis api worker
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Useful checks:

```powershell
docker compose exec api alembic current
docker compose exec postgres psql -U postgres -d humangate -c "select extversion from pg_extension where extname = 'vector';"
```

## Frontend Setup Plan

```text
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-query @tanstack/react-router @tanstack/react-table
npm install zod react-hook-form zustand motion
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs
npm install -D tailwindcss @tailwindcss/vite vite-tsconfig-paths vitest playwright
```

## Environment Variables

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/humangate
REDIS_URL=redis://localhost:6379/0

LLM_PRIMARY_PROVIDER=gemini
LLM_PRIMARY_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=

LOCAL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_FAST_MODEL=gemma3:4b
LOCAL_QUALITY_MODEL=qwen3:8b
LOCAL_ROUTER_MODEL=qwen2.5:3b

EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text-v2-moe
```

## First Milestone

1. Start PostgreSQL and Redis.
2. Run FastAPI health check.
3. Run React dashboard shell.
4. Connect dashboard to `/health`.
5. Connect WebSocket test endpoint.
6. Create first ticket.
7. Store first audit log.
