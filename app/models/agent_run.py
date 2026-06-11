import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AgentMode, AgentRunStatus, InputType, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_status_created_at", "status", "created_at"),
        Index("ix_agent_runs_ticket_id_created_at", "ticket_id", "created_at"),
    )

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="SET NULL"),
    )
    mode: Mapped[AgentMode] = mapped_column(
        enum_column(AgentMode, "agent_mode"),
        nullable=False,
    )
    input_type: Mapped[InputType] = mapped_column(
        enum_column(InputType, "input_type"),
        nullable=False,
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        enum_column(AgentRunStatus, "agent_run_status"),
        nullable=False,
        default=AgentRunStatus.QUEUED,
        server_default=AgentRunStatus.QUEUED.value,
    )
    final_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ticket = relationship("Ticket", back_populates="agent_runs")
    tool_calls = relationship(
        "ToolCall",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
    approval_requests = relationship(
        "ApprovalRequest",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
