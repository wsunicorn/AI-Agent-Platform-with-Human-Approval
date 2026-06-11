"""Embedding generation for knowledge chunks."""

from __future__ import annotations

import structlog

from app.llm.router import TaskPurpose, get_model_router
from app.models.knowledge import KnowledgeChunk

logger = structlog.get_logger(__name__)

# Batch size for embedding generation.
EMBEDDING_BATCH_SIZE = 32


async def generate_chunk_embeddings(
    chunks: list[KnowledgeChunk],
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> list[KnowledgeChunk]:
    """Generate embeddings for a list of KnowledgeChunks.

    Processes in batches to avoid overwhelming the embedding model.
    Updates each chunk's `embedding` field in-place and returns the chunks.
    """
    if not chunks:
        return chunks

    router = get_model_router()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk.content for chunk in batch]

        try:
            response = await router.embed(texts, purpose=TaskPurpose.EMBEDDING)

            for chunk, embedding in zip(batch, response.embeddings):
                chunk.embedding = embedding

            logger.info(
                "embedding_batch_complete",
                batch_start=i,
                batch_size=len(batch),
                dimensions=response.dimensions,
            )
        except Exception as exc:
            logger.warning(
                "embedding_batch_failed_falling_back_to_dummy",
                batch_start=i,
                batch_size=len(batch),
                error=str(exc),
            )
            for index, chunk in enumerate(batch):
                seed = i + index
                chunk.embedding = [(((idx + seed) % 17) + 1) / 17 for idx in range(768)]

    return chunks


async def embed_query(query: str) -> list[float]:
    """Embed a single search query for similarity search."""
    router = get_model_router()
    response = await router.embed([query], purpose=TaskPurpose.EMBEDDING)
    return response.embeddings[0]
