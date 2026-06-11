import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import Sensitivity, ToolCallStatus, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ToolCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("ix_tool_calls_agent_run_id_created_at", "agent_run_id", "created_at"),
        Index("ix_tool_calls_status_created_at", "status", "created_at"),
        Index("ix_tool_calls_tool_name_created_at", "tool_name", "created_at"),
    )

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    sensitivity: Mapped[Sensitivity] = mapped_column(
        enum_column(Sensitivity, "sensitivity"),
        nullable=False,
        default=Sensitivity.SAFE,
        server_default=Sensitivity.SAFE.value,
    )
    input_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[ToolCallStatus] = mapped_column(
        enum_column(ToolCallStatus, "tool_call_status"),
        nullable=False,
        default=ToolCallStatus.PROPOSED,
        server_default=ToolCallStatus.PROPOSED.value,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    timeout_ms: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent_run = relationship("AgentRun", back_populates="tool_calls")
    approval_request = relationship(
        "ApprovalRequest",
        back_populates="tool_call",
        uselist=False,
    )
