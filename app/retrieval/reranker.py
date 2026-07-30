"""LLM-based reranking of search results."""

from __future__ import annotations

import structlog

from app.llm import LLMMessage, LLMRequest, get_model_router
from app.llm.router import TaskPurpose
from app.retrieval.search import SearchResult

logger = structlog.get_logger(__name__)

_RERANK_SYSTEM = """You are a relevance scorer. Given a query and a document passage, 
score how relevant the passage is to answering the query.

Return a JSON object with a single field "score" between 0.0 and 1.0.
- 1.0 means perfectly relevant
- 0.0 means completely irrelevant

Only return the JSON object, nothing else."""

_RERANK_TEMPLATE = """Query: {query}

Passage: {passage}

Score the relevance (0.0 to 1.0):"""


async def rerank_results(
    query: str,
    results: list[SearchResult],
    top_k: int = 5,
) -> list[SearchResult]:
    """Rerank search results using an LLM to score relevance.

    Takes the candidate results and re-scores each passage against the query.
    Returns the top_k most relevant results.
    """
    if not results:
        return results

    if len(results) <= top_k:
        return results

    router = get_model_router()
    scored: list[tuple[SearchResult, float]] = []

    for result in results:
        passage = result.chunk.content[:1500]  # Truncate for context window.
        prompt = _RERANK_TEMPLATE.format(query=query, passage=passage)

        try:
            response_data = await router.complete_json(
                LLMRequest(
                    messages=[LLMMessage(role="user", content=prompt)],
                    model="",  # Router picks.
                    system_prompt=_RERANK_SYSTEM,
                    temperature=0.0,
                    max_tokens=50,
                ),
                purpose=TaskPurpose.RERANKING,
            )
            score = float(response_data.get("score", 0.0))
            scored.append((result, score))
        except Exception as exc:
            logger.warning(
                "rerank_score_failed",
                chunk_id=str(result.chunk.id),
                error=str(exc),
            )
            # Keep original score if reranking fails.
            scored.append((result, result.score))

    # Sort by reranked score descending.
    scored.sort(key=lambda x: x[1], reverse=True)

    logger.info(
        "reranking_complete",
        input_count=len(results),
        output_count=min(top_k, len(scored)),
    )

    return [
        SearchResult(
            chunk=r.chunk,
            score=s,
            method="reranked",
            document_title=r.document_title,
        )
        for r, s in scored[:top_k]
    ]
