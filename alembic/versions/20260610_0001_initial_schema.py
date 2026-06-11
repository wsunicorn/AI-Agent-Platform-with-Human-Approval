"""initial schema

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10 14:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260610_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def enum(*values: str, name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


ENUMS = [
    enum(
        "new",
        "triaged",
        "in_progress",
        "waiting_for_approval",
        "resolved",
        "closed",
        name="ticket_status",
    ),
    enum("low", "normal", "high", "urgent", name="priority"),
    enum("support_agent", "workflow_automation", name="agent_mode"),
    enum("ticket", "email", "instruction", name="input_type"),
    enum(
        "queued",
        "running",
        "waiting_for_approval",
        "completed",
        "failed",
        "cancelled",
        name="agent_run_status",
    ),
    enum("safe", "approval_required", "blocked", name="sensitivity"),
    enum(
        "proposed",
        "running",
        "completed",
        "failed",
        "denied",
        "waiting_for_approval",
        name="tool_call_status",
    ),
    enum(
        "proposed",
        "pending_review",
        "approved",
        "rejected",
        "edited",
        "executed",
        "cancelled",
        "failed",
        name="approval_status",
    ),
    enum("human", "agent", "system", "tool", name="actor_type"),
    enum(
        "policy",
        "faq",
        "playbook",
        "macro",
        "report_template",
        name="knowledge_document_type",
    ),
    enum("gemini", "openai", "anthropic", "ollama", "local", name="model_provider"),
    enum("hosted", "local", name="model_mode"),
    enum(
        "default",
        "routing",
        "drafting",
        "embedding",
        "fallback",
        "quality",
        name="model_purpose",
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    for enum in ENUMS:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "tickets",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", ENUMS[0], server_default="new", nullable=False),
        sa.Column("priority", ENUMS[1], server_default="normal", nullable=False),
        sa.Column("intent", sa.String(length=128), nullable=True),
        sa.Column("issue_type", sa.String(length=128), nullable=True),
        sa.Column(
            "extracted_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "search_tsvector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body, ''))",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
    )
    op.create_index("ix_tickets_priority_created_at", "tickets", ["priority", "created_at"])
    op.create_index(
        "ix_tickets_search_tsvector", "tickets", ["search_tsvector"], postgresql_using="gin"
    )
    op.create_index("ix_tickets_status_created_at", "tickets", ["status", "created_at"])

    op.create_table(
        "agent_runs",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mode", ENUMS[2], nullable=False),
        sa.Column("input_type", ENUMS[3], nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("status", ENUMS[4], server_default="queued", nullable=False),
        sa.Column("final_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name=op.f("fk_agent_runs_ticket_id_tickets"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_runs")),
    )
    op.create_index("ix_agent_runs_status_created_at", "agent_runs", ["status", "created_at"])
    op.create_index("ix_agent_runs_ticket_id_created_at", "agent_runs", ["ticket_id", "created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("actor_type", ENUMS[8], nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(
        "ix_audit_logs_entity_timestamp", "audit_logs", ["entity_type", "entity_id", "timestamp"]
    )
    op.create_index("ix_audit_logs_event_type_timestamp", "audit_logs", ["event_type", "timestamp"])

    op.create_table(
        "knowledge_documents",
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("document_type", ENUMS[9], server_default="policy", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_documents")),
        sa.UniqueConstraint("checksum", name="uq_knowledge_documents_checksum"),
    )
    op.create_index(
        "ix_knowledge_documents_document_type_created_at",
        "knowledge_documents",
        ["document_type", "created_at"],
    )

    op.create_table(
        "model_configs",
        sa.Column("provider", ENUMS[10], nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("endpoint_url", sa.String(length=500), nullable=True),
        sa.Column("mode", ENUMS[11], nullable=False),
        sa.Column("purpose", ENUMS[12], nullable=False),
        sa.Column("temperature", sa.Float(), server_default="0.2", nullable=False),
        sa.Column("max_tokens", sa.Integer(), server_default="2048", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_configs")),
        sa.UniqueConstraint(
            "provider", "model_name", "purpose", name="uq_model_configs_provider_model_purpose"
        ),
    )
    op.create_index(
        "ix_model_configs_provider_purpose_default",
        "model_configs",
        ["provider", "purpose", "is_default"],
    )

    op.create_table(
        "tool_calls",
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("sensitivity", ENUMS[5], server_default="safe", nullable=False),
        sa.Column(
            "input_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", ENUMS[6], server_default="proposed", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            name=op.f("fk_tool_calls_agent_run_id_agent_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_calls")),
    )
    op.create_index(
        "ix_tool_calls_agent_run_id_created_at", "tool_calls", ["agent_run_id", "created_at"]
    )
    op.create_index("ix_tool_calls_status_created_at", "tool_calls", ["status", "created_at"])
    op.create_index("ix_tool_calls_tool_name_created_at", "tool_calls", ["tool_name", "created_at"])

    op.create_table(
        "approval_requests",
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column(
            "proposed_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("edited_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_reason", sa.Text(), nullable=False),
        sa.Column("status", ENUMS[7], server_default="pending_review", nullable=False),
        sa.Column("reviewer_id", sa.String(length=255), nullable=True),
        sa.Column("reviewer_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            name=op.f("fk_approval_requests_agent_run_id_agent_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tool_call_id"],
            ["tool_calls.id"],
            name=op.f("fk_approval_requests_tool_call_id_tool_calls"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approval_requests")),
        sa.UniqueConstraint("tool_call_id", name="uq_approval_requests_tool_call_id"),
    )
    op.create_index(
        "ix_approval_requests_agent_run_id_created_at",
        "approval_requests",
        ["agent_run_id", "created_at"],
    )
    op.create_index(
        "ix_approval_requests_status_created_at",
        "approval_requests",
        ["status", "created_at"],
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("knowledge_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_tsvector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', coalesce(content, ''))", persisted=True),
            nullable=True,
        ),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_document_id"],
            ["knowledge_documents.id"],
            name=op.f("fk_knowledge_chunks_knowledge_document_id_knowledge_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_chunks")),
        sa.UniqueConstraint(
            "knowledge_document_id",
            "chunk_index",
            name="uq_knowledge_chunks_document_index",
        ),
    )
    op.create_index(
        "ix_knowledge_chunks_content_tsvector",
        "knowledge_chunks",
        ["content_tsvector"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_knowledge_chunks_document_id", "knowledge_chunks", ["knowledge_document_id"]
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64) "
        "WHERE embedding IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.drop_table("knowledge_chunks")
    op.drop_table("approval_requests")
    op.drop_table("tool_calls")
    op.drop_table("model_configs")
    op.drop_table("knowledge_documents")
    op.drop_table("audit_logs")
    op.drop_table("agent_runs")
    op.drop_table("tickets")

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind, checkfirst=True)
