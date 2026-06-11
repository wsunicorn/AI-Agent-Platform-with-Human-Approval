"""Search: full-text, vector, and hybrid search with RRF fusion."""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.retrieval.embedding import embed_query

logger = structlog.get_logger(__name__)


class SearchResult:
    """A single search result with score and metadata."""

    def __init__(
        self,
        chunk: KnowledgeChunk,
        score: float,
        method: str,
    ) -> None:
        self.chunk = chunk
        self.score = score
        self.method = method

    def __repr__(self) -> str:
        return f"SearchResult(score={self.score:.4f}, method={self.method})"


async def full_text_search(
    session: AsyncSession,
    query: str,
    limit: int = 20,
    doc_type: str | None = None,
) -> list[SearchResult]:
    """PostgreSQL full-text search using tsvector."""
    ts_query = func.plainto_tsquery("english", query)

    stmt = (
        select(
            KnowledgeChunk,
            func.ts_rank(
                func.to_tsvector("english", KnowledgeChunk.content),
                ts_query,
            ).label("rank"),
        )
        .where(
            func.to_tsvector("english", KnowledgeChunk.content).op("@@")(ts_query)
        )
        .order_by(text("rank DESC"))
        .limit(limit)
    )

    if doc_type:
        stmt = stmt.join(KnowledgeDocument).where(
            KnowledgeDocument.doc_type == doc_type
        )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        SearchResult(chunk=row[0], score=float(row[1]), method="full_text")
        for row in rows
    ]


async def vector_search(
    session: AsyncSession,
    query: str,
    limit: int = 20,
    doc_type: str | None = None,
) -> list[SearchResult]:
    """pgvector cosine similarity search."""
    query_embedding = await embed_query(query)

    # Use cosine distance operator <=> for pgvector.
    stmt = (
        select(
            KnowledgeChunk,
            KnowledgeChunk.embedding.cosine_distance(query_embedding).label(
                "distance"
            ),
        )
        .where(KnowledgeChunk.embedding.isnot(None))
        .order_by(text("distance ASC"))
        .limit(limit)
    )

    if doc_type:
        stmt = stmt.join(KnowledgeDocument).where(
            KnowledgeDocument.doc_type == doc_type
        )

    result = await session.execute(stmt)
    rows = result.all()

    # Convert distance to similarity score (1 - distance).
    return [
        SearchResult(
            chunk=row[0],
            score=max(0, 1.0 - float(row[1])),
            method="vector",
        )
        for row in rows
    ]


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]],
    k: int = 60,
) -> list[SearchResult]:
    """Fuse multiple ranked result lists using Reciprocal Rank Fusion (RRF).

    RRF score = sum(1 / (k + rank)) for each list the document appears in.
    """
    scores: dict[UUID, float] = {}
    chunk_map: dict[UUID, SearchResult] = {}

    for results in result_lists:
        for rank, result in enumerate(results):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score

            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = result

    # Sort by fused score descending.
    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    return [
        SearchResult(
            chunk=chunk_map[cid].chunk,
            score=scores[cid],
            method="hybrid_rrf",
        )
        for cid in sorted_ids
    ]


async def hybrid_search(
    session: AsyncSession,
    query: str,
    limit: int = 10,
    full_text_limit: int = 30,
    vector_limit: int = 30,
    doc_type: str | None = None,
) -> list[SearchResult]:
    """Hybrid search combining full-text and vector search with RRF fusion."""
    logger.info("hybrid_search_start", query=query[:100])

    # Run both searches.
    ft_results = await full_text_search(
        session, query, limit=full_text_limit, doc_type=doc_type
    )
    vec_results = await vector_search(
        session, query, limit=vector_limit, doc_type=doc_type
    )

    logger.info(
        "hybrid_search_components",
        full_text_count=len(ft_results),
        vector_count=len(vec_results),
    )

    # Fuse results.
    fused = reciprocal_rank_fusion([ft_results, vec_results])

    logger.info("hybrid_search_complete", fused_count=len(fused), limit=limit)

    return fused[:limit]
