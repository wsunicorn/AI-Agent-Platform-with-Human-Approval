"""WebSocket API endpoints for live updates."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.redis import get_redis
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger("humangate.websockets")

router = APIRouter(tags=["websockets"])

# Shared manager instances.
_agent_run_manager = WebSocketManager()
_approval_manager = WebSocketManager()
_notification_manager = WebSocketManager()

_redis_listener_task: asyncio.Task | None = None


def get_agent_run_manager() -> WebSocketManager:
    return _agent_run_manager


def get_approval_manager() -> WebSocketManager:
    return _approval_manager


def get_notification_manager() -> WebSocketManager:
    return _notification_manager


async def redis_event_listener() -> None:
    """Listen to Redis Pub/Sub channels and forward events to WebSockets."""
    logger.info("Starting Redis event listener background task...")
    
    redis = get_redis()
    pubsub = redis.pubsub()
    settings = get_settings()
    
    # Subscribe to the main events channel
    await pubsub.subscribe(settings.redis_events_channel)
    
    try:
        while True:
            # We use a non-blocking check to avoid hanging forever on disconnect
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
            if message and message.get("type") == "message":
                try:
                    payload_str = message.get("data")
                    if not payload_str:
                        continue
                    
                    if isinstance(payload_str, bytes):
                        payload_str = payload_str.decode("utf-8")
                        
                    envelope = json.loads(payload_str)
                    
                    event_type = envelope.get("event_type")
                    entity_type = envelope.get("entity_type")
                    entity_id = envelope.get("entity_id")
                    payload = envelope.get("payload", {})
                    created_at = envelope.get("created_at")
                    
                    # Unpack audit_log.created to get the real event type
                    real_event_type = event_type
                    real_entity_type = entity_type
                    real_entity_id = entity_id
                    metadata = {}
                    
                    if event_type == "audit_log.created":
                        real_event_type = payload.get("event_type")
                        real_entity_type = payload.get("entity_type")
                        real_entity_id = payload.get("entity_id")
                        metadata = payload.get("metadata", {})
                    
                    ws_event = {
                        "type": real_event_type,
                        "data": {
                            "entity_type": real_entity_type,
                            "entity_id": real_entity_id,
                            **metadata,
                        },
                        "timestamp": created_at,
                    }
                    
                    # Identify agent run ID
                    run_id = None
                    if real_entity_type == "agent_run":
                        run_id = real_entity_id
                    elif "agent_run_id" in metadata:
                        run_id = metadata["agent_run_id"]
                    
                    # Broadcast run events to `/ws/agent-runs/{run_id}`
                    if run_id:
                        await _agent_run_manager.broadcast(topic=str(run_id), message=ws_event)
                    else:
                        # Broadcast to all connected run connections if no run_id is found
                        for topic in list(_agent_run_manager._connections.keys()):
                            await _agent_run_manager.broadcast(topic=topic, message=ws_event)
                            
                    # Broadcast to approvals manager if event is approval related
                    if real_event_type.startswith("approval.") or real_entity_type == "approval_request":
                        await _approval_manager.broadcast(topic="approvals", message=ws_event)
                        
                    # Broadcast to general notifications
                    await _notification_manager.broadcast(topic="notifications", message=ws_event)
                    
                except Exception as exc:
                    logger.error("Error processing Redis message in websocket listener: %s", exc)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        logger.info("Redis event listener background task cancelled.")
    except Exception as exc:
        logger.exception("Redis event listener encountered unexpected error: %s", exc)


def start_redis_listener_task() -> None:
    global _redis_listener_task
    if _redis_listener_task is None:
        _redis_listener_task = asyncio.create_task(redis_event_listener())


def stop_redis_listener_task() -> None:
    global _redis_listener_task
    if _redis_listener_task is not None:
        _redis_listener_task.cancel()
        _redis_listener_task = None


@router.websocket("/ws/agent-runs/{run_id}")
async def ws_agent_run(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint for live agent run events."""
    await _agent_run_manager.connect(websocket, topic=run_id)
    try:
        while True:
            # Keep connection alive. Listen for client messages (pings).
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _agent_run_manager.disconnect(websocket, topic=run_id)
    except Exception:
        _agent_run_manager.disconnect(websocket, topic=run_id)


@router.websocket("/ws/approvals")
async def ws_approvals(websocket: WebSocket) -> None:
    """WebSocket endpoint for live approval notifications."""
    await _approval_manager.connect(websocket, topic="approvals")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _approval_manager.disconnect(websocket, topic="approvals")
    except Exception:
        _approval_manager.disconnect(websocket, topic="approvals")


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket) -> None:
    """WebSocket endpoint for general notifications."""
    await _notification_manager.connect(websocket, topic="notifications")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _notification_manager.disconnect(websocket, topic="notifications")
    except Exception:
        _notification_manager.disconnect(websocket, topic="notifications")

