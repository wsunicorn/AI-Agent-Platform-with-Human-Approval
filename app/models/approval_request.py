import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ApprovalStatus, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ApprovalRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        UniqueConstraint("tool_call_id", name="uq_approval_requests_tool_call_id"),
        Index("ix_approval_requests_status_created_at", "status", "created_at"),
        Index("ix_approval_requests_agent_run_id_created_at", "agent_run_id", "created_at"),
    )

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tool_calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    proposed_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    edited_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    risk_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        enum_column(ApprovalStatus, "approval_status"),
        nullable=False,
        default=ApprovalStatus.PENDING_REVIEW,
        server_default=ApprovalStatus.PENDING_REVIEW.value,
    )
    reviewer_id: Mapped[str | None] = mapped_column(String(255))
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent_run = relationship("AgentRun", back_populates="approval_requests")
    tool_call = relationship("ToolCall", back_populates="approval_request")
