from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.serialization import to_jsonable
from app.models import ActorType, AuditLog
from app.services.events import EventEnvelope, EventService


class AuditService:
    def __init__(self, session: AsyncSession, events: EventService | None = None) -> None:
        self.session = session
        self.events = events or EventService()

    async def record(
        self,
        *,
        actor_type: ActorType,
        actor_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        publish: bool = True,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=to_jsonable(before_state),
            after_state=to_jsonable(after_state),
            event_metadata=to_jsonable(metadata or {}),
        )
        self.session.add(audit_log)
        await self.session.flush()

        if publish:
            await self.publish_created(audit_log)

        return audit_log

    async def publish_created(self, audit_log: AuditLog) -> EventEnvelope:
        return await self.events.publish(
            event_type="audit_log.created",
            entity_type="audit_log",
            entity_id=str(audit_log.id),
            actor_id=audit_log.actor_id,
            payload={
                "event_type": audit_log.event_type,
                "entity_type": audit_log.entity_type,
                "entity_id": audit_log.entity_id,
                "metadata": audit_log.event_metadata,
            },
            topics=[
                "audit_logs",
                f"{audit_log.entity_type}.{audit_log.entity_id}",
            ],
        )
