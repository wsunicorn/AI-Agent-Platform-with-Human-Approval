"""Context packing with source citations for LLM consumption."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.search import SearchResult


@dataclass
class Citation:
    """A numbered citation reference."""

    index: int
    document_title: str
    heading: str
    chunk_id: str
    score: float


@dataclass
class PackedContext:
    """Context window packed with numbered citations."""

    context_text: str
    citations: list[Citation]
    total_tokens_estimate: int


def pack_context(
    results: list[SearchResult],
    max_tokens: int = 4000,
    include_scores: bool = False,
) -> PackedContext:
    """Pack search results into a formatted context string with citations.

    Format:
    [1] (Heading / Title)
    Content text...

    [2] (Heading / Title)
    Content text...

    Sources:
    [1] Document Title - Section Heading (relevance: 0.85)
    [2] Document Title - Section Heading (relevance: 0.72)
    """
    context_parts: list[str] = []
    citations: list[Citation] = []
    token_count = 0

    for i, result in enumerate(results):
        chunk = result.chunk
        heading = getattr(chunk, "heading", "") or "Untitled"

        # Estimate tokens for this chunk.
        chunk_tokens = len(chunk.content) // 4  # Rough estimate.

        if token_count + chunk_tokens > max_tokens:
            # Truncate this chunk to fit remaining budget.
            remaining_chars = (max_tokens - token_count) * 4
            if remaining_chars <= 100:
                break
            content = chunk.content[:remaining_chars] + "..."
        else:
            content = chunk.content

        ref_num = i + 1
        context_parts.append(f"[{ref_num}] ({heading})\n{content}")

        # Get document title if available through relationship.
        doc_title = heading  # Fallback.
        if hasattr(chunk, "document") and chunk.document:
            doc_title = chunk.document.title

        citations.append(
            Citation(
                index=ref_num,
                document_title=doc_title,
                heading=heading,
                chunk_id=str(chunk.id),
                score=result.score,
            )
        )

        token_count += chunk_tokens

    # Build context text.
    context_text = "\n\n".join(context_parts)

    # Append citation footer.
    if citations:
        footer_parts = ["\n\nSources:"]
        for cite in citations:
            line = f"[{cite.index}] {cite.document_title}"
            if cite.heading and cite.heading != cite.document_title:
                line += f" - {cite.heading}"
            if include_scores:
                line += f" (relevance: {cite.score:.2f})"
            footer_parts.append(line)
        context_text += "\n".join(footer_parts)

    return PackedContext(
        context_text=context_text,
        citations=citations,
        total_tokens_estimate=token_count,
    )
