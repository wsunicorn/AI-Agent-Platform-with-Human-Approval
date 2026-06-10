# LLM and Retrieval Design

## LLM Strategy

The project uses a Gemini-free-first strategy with local fallback.

Primary provider:

- Google Gemini Developer API

Primary model:

- `gemini-3.1-flash-lite`

Optional stronger hosted model:

- `gemini-3.5-flash`

Advanced experiment model:

- `gemini-3.1-pro-preview`

Local provider:

- Ollama

## Local Machine Profile

```text
Machine: Acer Nitro AN515-58
CPU: Intel Core i5-12500H, 12 cores / 16 threads
RAM: 32GB
GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4GB VRAM
Runtime: Ollama installed
```

## Current Local Models

```text
gemma3:4b
qwen3:8b
qwen2.5:7b
qwen2.5:3b
nomic-embed-text-v2-moe
```

## Recommended Local Defaults

- Fast local fallback: `gemma3:4b`
- Higher-quality local fallback: `qwen3:8b`
- Fast router/extractor: `qwen2.5:3b`
- Installed local embedding: `nomic-embed-text-v2-moe`

## Recommended Next Pulls

```text
ollama pull gemma3n:e4b
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
```

## Model Routing

```text
classification/extraction:
  primary: gemini-3.1-flash-lite
  local fallback: gemma3:4b or qwen2.5:3b

policy retrieval query rewriting:
  primary: gemini-3.1-flash-lite
  local fallback: gemma3:4b

draft response:
  primary: gemini-3.1-flash-lite
  optional hosted escalation: gemini-3.5-flash
  local quality fallback: qwen3:8b

approval risk analysis:
  primary: gemini-3.1-flash-lite with higher thinking level
  local quality fallback: qwen3:8b

final customer-facing message:
  primary: gemini-3.1-flash-lite
  optional hosted escalation: gemini-3.5-flash
  local private fallback: gemma3:4b or qwen3:8b

report generation:
  primary: gemini-3.1-flash-lite
  local fallback: qwen3:8b
```

## Environment Configuration

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

## Retrieval Architecture

```text
document ingestion
-> markdown/html-aware parsing
-> chunking
-> embedding
-> PostgreSQL full-text index
-> pgvector HNSW index
-> hybrid search
-> reranking
-> context packing with citations
```

## Retrieval Defaults

- Use PostgreSQL full-text search for exact terms.
- Use pgvector for semantic search.
- Fuse keyword and vector results with Reciprocal Rank Fusion.
- Rerank the top 20-50 results.
- Return source citations with every retrieved chunk.

## Privacy Rules

- Gemini free tier is fine for demo, mock data, and redacted test data.
- Do not send real support tickets with PII to Gemini free tier unless data-use terms are acceptable.
- Use local models for private mode.
- Redact secrets and PII from traces.

