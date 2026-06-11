from typing import Any

from sqlalchemy import Computed, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import Priority, TicketStatus, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_status_created_at", "status", "created_at"),
        Index("ix_tickets_priority_created_at", "priority", "created_at"),
        Index("ix_tickets_search_tsvector", "search_tsvector", postgresql_using="gin"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False, default="email")
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        enum_column(TicketStatus, "ticket_status"),
        nullable=False,
        default=TicketStatus.NEW,
        server_default=TicketStatus.NEW.value,
    )
    priority: Mapped[Priority] = mapped_column(
        enum_column(Priority, "priority"),
        nullable=False,
        default=Priority.NORMAL,
        server_default=Priority.NORMAL.value,
    )
    intent: Mapped[str | None] = mapped_column(String(128))
    issue_type: Mapped[str | None] = mapped_column(String(128))
    extracted_entities: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    search_tsvector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body, ''))",
            persisted=True,
        ),
    )

    agent_runs = relationship("AgentRun", back_populates="ticket")
