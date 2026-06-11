"""Knowledge base REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import (
    ApiResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentOut,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from app.models.knowledge import KnowledgeDocument

router = APIRouter(prefix="/knowledge-documents", tags=["knowledge"])


@router.post("", response_model=ApiResponse[KnowledgeDocumentOut], status_code=201)
async def create_document(
    body: KnowledgeDocumentCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.retrieval.ingestion import ingest_document

    doc = await ingest_document(
        session=session,
        title=body.title,
        content=body.content,
        doc_type=body.doc_type,
        tags=body.tags,
        source_url=body.source_url,
    )
    await session.commit()
    return {"data": KnowledgeDocumentOut.model_validate(doc)}


@router.get("", response_model=ApiResponse[list[KnowledgeDocumentOut]])
async def list_documents(
    doc_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> dict:
    query = select(KnowledgeDocument).order_by(
        KnowledgeDocument.created_at.desc()
    )
    if doc_type:
        query = query.where(KnowledgeDocument.document_type == doc_type)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    docs = result.scalars().all()
    return {
        "data": [KnowledgeDocumentOut.model_validate(d) for d in docs],
        "meta": {"limit": limit, "offset": offset},
    }


@router.get("/{document_id}", response_model=ApiResponse[KnowledgeDocumentOut])
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"data": KnowledgeDocumentOut.model_validate(doc)}


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    result = await session.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await session.delete(doc)
    await session.commit()


@router.post("/search", response_model=ApiResponse[list[KnowledgeSearchResult]])
async def search_knowledge(
    body: KnowledgeSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.retrieval.search import hybrid_search

    results = await hybrid_search(
        session=session,
        query=body.query,
        limit=body.limit,
        doc_type=body.doc_type,
    )
    return {
        "data": [
            KnowledgeSearchResult(
                chunk_content=r.chunk.content[:500],
                score=r.score,
                method=r.method,
                document_title=getattr(r.chunk, "heading", None),
                heading=getattr(r.chunk, "heading", None),
            )
            for r in results
        ]
    }
