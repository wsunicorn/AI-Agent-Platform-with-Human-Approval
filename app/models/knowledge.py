import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import KnowledgeDocumentType, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("checksum", name="uq_knowledge_documents_checksum"),
        Index("ix_knowledge_documents_document_type_created_at", "document_type", "created_at"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default=text("'{}'::text[]"),
    )
    document_type: Mapped[KnowledgeDocumentType] = mapped_column(
        enum_column(KnowledgeDocumentType, "knowledge_document_type"),
        nullable=False,
        default=KnowledgeDocumentType.POLICY,
        server_default=KnowledgeDocumentType.POLICY.value,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_document_id",
            "chunk_index",
            name="uq_knowledge_chunks_document_index",
        ),
        Index("ix_knowledge_chunks_document_id", "knowledge_document_id"),
        Index("ix_knowledge_chunks_content_tsvector", "content_tsvector", postgresql_using="gin"),
    )

    knowledge_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_tsvector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(content, ''))", persisted=True),
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    embedding_model: Mapped[str | None] = mapped_column(String(255))
    token_count: Mapped[int | None] = mapped_column(Integer)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    document = relationship("KnowledgeDocument", back_populates="chunks")
