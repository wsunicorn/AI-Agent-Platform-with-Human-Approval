from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.serialization import to_jsonable


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, topic: str) -> None:
        await websocket.accept()
        self._connections[topic].add(websocket)

    def disconnect(self, websocket: WebSocket, topic: str) -> None:
        topic_connections = self._connections.get(topic)
        if not topic_connections:
            return

        topic_connections.discard(websocket)
        if not topic_connections:
            self._connections.pop(topic, None)

    async def broadcast(self, topic: str, message: dict[str, Any]) -> int:
        connections = list(self._connections.get(topic, set()))
        delivered = 0

        for websocket in connections:
            if websocket.client_state != WebSocketState.CONNECTED:
                self.disconnect(websocket, topic)
                continue

            try:
                await websocket.send_json(to_jsonable(message))
                delivered += 1
            except RuntimeError:
                self.disconnect(websocket, topic)

        return delivered

    async def broadcast_many(self, topics: list[str], message: dict[str, Any]) -> int:
        delivered = 0
        for topic in topics:
            delivered += await self.broadcast(topic, message)
        return delivered

    def connection_count(self, topic: str | None = None) -> int:
        if topic is not None:
            return len(self._connections.get(topic, set()))
        return sum(len(connections) for connections in self._connections.values())


websocket_manager = WebSocketManager()
