"""Markdown-aware document chunking."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.knowledge import KnowledgeChunk


# Target chunk sizes in characters (rough proxy for tokens at ~4 chars/token).
DEFAULT_CHUNK_SIZE = 2048  # ~512 tokens
DEFAULT_CHUNK_OVERLAP = 256  # ~64 tokens

# Heading patterns for section boundary detection.
_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _split_by_headings(content: str) -> list[tuple[str, str]]:
    """Split content into sections by markdown headings.

    Returns list of (heading, body) tuples.
    """
    parts = _HEADING_RE.split(content)
    headings = _HEADING_RE.findall(content)

    sections: list[tuple[str, str]] = []

    # Content before the first heading.
    if parts and parts[0].strip():
        sections.append(("", parts[0].strip()))

    for i, heading in enumerate(headings):
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading.strip(), body))

    return sections


def _split_text_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by paragraph boundaries."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    paragraphs = re.split(r"\n\n+", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 2 > chunk_size and current:
            chunks.append(current.strip())
            # Overlap: keep the last `overlap` characters.
            if overlap > 0 and len(current) > overlap:
                current = current[-overlap:] + "\n\n" + para
            else:
                current = para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_document(
    doc_id: UUID,
    content: str,
    title: str = "",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[KnowledgeChunk]:
    """Chunk a document into KnowledgeChunk records.

    Strategy:
    1. Split by markdown headings (preserves section boundaries).
    2. Within each section, split by paragraph boundaries with overlap.
    3. Prepend section heading to each chunk for context.
    """
    sections = _split_by_headings(content)
    chunks: list[KnowledgeChunk] = []
    chunk_index = 0
    now = datetime.now(timezone.utc)

    for heading, body in sections:
        if not body.strip():
            continue

        prefix = f"{heading}\n\n" if heading else ""
        adjusted_size = chunk_size - len(prefix)

        text_chunks = _split_text_chunks(body, adjusted_size, overlap)

        for text in text_chunks:
            chunk_content = prefix + text
            chunk = KnowledgeChunk(
                id=uuid4(),
                document_id=doc_id,
                content=chunk_content,
                chunk_index=chunk_index,
                heading=heading or title,
                token_count=len(chunk_content) // 4,  # Rough estimate
                created_at=now,
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks
