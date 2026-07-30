# LLM and Retrieval Design

## LLM Strategy

Gemini-first with local Ollama fallback, both called through LiteLLM
(`app/llm/gemini.py`, `app/llm/ollama.py`). Routing is entirely code-defined
in `app/llm/router.py:_DEFAULT_ROUTING` — there is no database- or
env-driven override of the fallback chains themselves (the `model_configs`
table exists and is editable through the Settings screen, but
`ModelRouter` never reads it; see [`DATA_MODEL.md`](DATA_MODEL.md)).

## Actual routing table (`_DEFAULT_ROUTING`)

| `TaskPurpose` | Chain (tried in order) |
| --- | --- |
| `classification` | `gemini/gemini-3.1-flash-lite` → `ollama/gemma3:4b` → `ollama/qwen2.5:3b` |
| `extraction` | same as `classification` |
| `drafting` | `gemini/gemini-3.1-flash-lite` → `ollama/qwen3:8b` → `ollama/gemma3:4b` |
| `routing` | `gemini/gemini-3.1-flash-lite` → `ollama/qwen2.5:3b` |
| `quality` | `gemini/gemini-3.5-flash` → `gemini/gemini-3.1-flash-lite` → `ollama/qwen3:8b` |
| `embedding` | `ollama/nomic-embed-text-v2-moe` (local only, no hosted fallback) |
| `reranking` | `gemini/gemini-3.1-flash-lite` → `ollama/gemma3:4b` |
| `default` | `gemini/gemini-3.1-flash-lite` → `ollama/gemma3:4b` |

`ModelRouter.complete` tries each entry in order until one succeeds, catching
any exception and moving to the next; if every entry fails, it raises
`RuntimeError` with all the collected errors. The Gemini provider is only
registered at all if `GEMINI_API_KEY` is set; without a key, every purpose
above silently falls through to its Ollama entries.

### PII redaction before hosted calls

`ModelRouter.complete` runs `PIIRedactor.redact` on every message (and the
system prompt) before calling any **non-Ollama** provider, and skips
redaction entirely for `ollama` calls (local, so nothing leaves the machine).
It builds a deep copy of the request first (`request.model_copy(deep=True)`)
so redaction never mutates the caller's original message objects — this
matters because the same `LLMRequest` object can be retried against multiple
providers in the fallback chain, and a shallow copy would have let the second
attempt see already-redacted text even for a purely-local fallback.

## Local Machine Profile (development reference)

```text
Machine: Acer Nitro AN515-58
CPU: Intel Core i5-12500H, 12 cores / 16 threads
RAM: 32GB
GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4GB VRAM
Runtime: Ollama installed
```

Models expected to be pulled locally for the fallback chains above:
`gemma3:4b`, `qwen3:8b`, `qwen2.5:3b`, `nomic-embed-text-v2-moe`. (`qwen2.5:7b`
is not referenced by any routing chain today.)

## Environment Configuration

The actual `Settings` fields read by `app/core/config.py` (everything else
is ignored — `extra="ignore"`):

```text
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
LOCAL_EMBEDDING_DIMENSIONS=768
```

Note that `llm_primary_provider`, `llm_primary_model`,
`local_fast_model`/`local_quality_model`/`local_router_model` are read into
`Settings` but **not actually consulted by `ModelRouter`** — the router uses
its own hardcoded `_DEFAULT_ROUTING` table above instead of building the
chain from these settings. They currently only affect anything that reads
`get_settings()` directly (e.g. `GeminiProvider`/`OllamaProvider`
construction uses `gemini_api_key` / `ollama_base_url`). Escalation/experiment
model names (`gemini-3.5-flash` for the `quality` purpose) are inline in the
routing table, not environment variables — there's no
`LLM_ESCALATION_MODEL`-style setting in the codebase.

## Retrieval Architecture

```text
document ingestion (app/retrieval/ingestion.py)
-> SHA-256 checksum computed; duplicate content (same checksum) rejected
-> markdown-heading-aware chunking (app/retrieval/chunking.py, "#"-style headings)
-> embedding generation (ModelRouter.embed, TaskPurpose.EMBEDDING)
-> chunk + tsvector (generated column) + embedding stored in knowledge_chunks
-> hybrid_search: full-text (tsvector) + vector (pgvector cosine) in parallel
-> Reciprocal Rank Fusion merges the two ranked lists
-> optional LLM reranking (only when candidates > top_k)
-> pack_context adds numbered [1]/[2]/... citations with document titles
```

Chunking is markdown-heading-aware only — there is no HTML parser in
`app/retrieval/`, despite documents being ingestible with arbitrary content.

### Actual defaults, not aspirational ranges

- `hybrid_search(limit=10, full_text_limit=30, vector_limit=30)` by default;
  `retrieve_policy_context` (the LangGraph node) calls it with `limit=20`.
- If vector search returns zero rows (or throws), `hybrid_search` returns the
  full-text results directly rather than fusing an empty list — this also
  degrades gracefully if pgvector/embeddings aren't available.
- `rerank_results(top_k=5)` — reranks whatever `hybrid_search` returned (≤20
  in the support-agent path) down to the 5 most relevant by LLM score, but
  only bothers calling the LLM at all when there are more candidates than
  `top_k`.
- Reranking scores each candidate independently with one LLM call per
  passage (not a single batched call), so it costs one call per candidate
  chunk — worth knowing before pointing this at hosted Gemini during a demo
  with a very large knowledge base.

## Privacy Rules

- Gemini's free tier is fine for demo/mock data and PII-redacted traffic.
- Real support tickets with PII shouldn't go to Gemini's free tier unless its
  data-use terms are acceptable for your use case — the `PIIRedactor` reduces
  but does not eliminate that risk (it's pattern-based redaction, not a
  guarantee).
- Ollama calls skip redaction entirely since nothing leaves the machine.
