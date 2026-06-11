import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.serialization import to_jsonable


class EventEnvelope(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    actor_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventService:
    def __init__(self, redis: Redis | None = None) -> None:
        self.redis = redis or get_redis()
        self.settings = get_settings()

    async def publish(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
        actor_id: str | None = None,
        topics: list[str] | None = None,
    ) -> EventEnvelope:
        envelope = EventEnvelope(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=to_jsonable(payload or {}),
            actor_id=actor_id,
        )
        message = envelope.model_dump_json()

        await self.redis.xadd(
            self.settings.redis_events_stream,
            {"event": message},
            maxlen=self.settings.redis_events_stream_maxlen,
            approximate=True,
        )
        await self.redis.publish(self.settings.redis_events_channel, message)

        for topic in topics or []:
            await self.redis.publish(self.topic_channel(topic), message)

        return envelope

    async def publish_raw(self, topic: str, payload: dict[str, Any]) -> None:
        await self.redis.publish(self.topic_channel(topic), json.dumps(to_jsonable(payload)))

    def topic_channel(self, topic: str) -> str:
        return f"{self.settings.redis_events_channel}.{topic}"
