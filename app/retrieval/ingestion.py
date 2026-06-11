"""Document ingestion for the knowledge base."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import KnowledgeDocumentType
from app.models.knowledge import KnowledgeDocument
from app.retrieval.chunking import chunk_document
from app.retrieval.embedding import generate_chunk_embeddings

logger = structlog.get_logger(__name__)


async def ingest_document(
    session: AsyncSession,
    title: str,
    content: str,
    doc_type: KnowledgeDocumentType = KnowledgeDocumentType.POLICY,
    tags: list[str] | None = None,
    source_url: str | None = None,
) -> KnowledgeDocument:
    """Ingest a document into the knowledge base.

    Steps:
    1. Store the KnowledgeDocument record.
    2. Chunk the content.
    3. Generate embeddings for each chunk.
    4. Store all chunks with embeddings.
    """
    doc_id = uuid4()
    now = datetime.now(timezone.utc)

    doc = KnowledgeDocument(
        id=doc_id,
        title=title,
        content=content,
        document_type=doc_type,
        tags=tags or [],
        source_url=source_url,
        created_at=now,
        updated_at=now,
    )
    session.add(doc)
    await session.flush()

    logger.info("document_ingestion_started", doc_id=str(doc_id), title=title)

    try:
        # Chunk the document.
        chunks = chunk_document(
            doc_id=doc_id,
            content=content,
            title=title,
        )
        logger.info("document_chunked", doc_id=str(doc_id), chunk_count=len(chunks))

        # Generate embeddings.
        chunks_with_embeddings = await generate_chunk_embeddings(chunks)
        logger.info(
            "embeddings_generated",
            doc_id=str(doc_id),
            count=len(chunks_with_embeddings),
        )

        # Store all chunks.
        for chunk in chunks_with_embeddings:
            session.add(chunk)

        doc.updated_at = datetime.now(timezone.utc)

        await session.flush()
        logger.info("document_ingestion_complete", doc_id=str(doc_id))

    except Exception as exc:
        doc.updated_at = datetime.now(timezone.utc)
        await session.flush()
        logger.error(
            "document_ingestion_failed",
            doc_id=str(doc_id),
            error=str(exc),
        )
        raise

    return doc


async def get_document(
    session: AsyncSession, doc_id: str
) -> KnowledgeDocument | None:
    """Retrieve a document by ID."""
    result = await session.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    return result.scalar_one_or_none()


async def list_documents(
    session: AsyncSession,
    doc_type: KnowledgeDocumentType | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[KnowledgeDocument]:
    """List all documents with optional type filter."""
    query = select(KnowledgeDocument).order_by(
        KnowledgeDocument.created_at.desc()
    )
    if doc_type:
        query = query.where(KnowledgeDocument.doc_type == doc_type)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all())
