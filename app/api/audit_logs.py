"""Audit log REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import ApiResponse, AuditLogOut
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=ApiResponse[list[AuditLogOut]])
async def list_audit_logs(
    agent_run_id: str | None = None,
    entity_type: str | None = None,
    actor_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> dict:
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if agent_run_id:
        from sqlalchemy import or_
        query = query.where(
            or_(
                AuditLog.event_metadata["agent_run_id"].astext == agent_run_id,
                AuditLog.entity_id == agent_run_id
            )
        )
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)
    if action:
        query = query.where(AuditLog.event_type == action)

    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    logs = result.scalars().all()
    return {
        "data": [AuditLogOut.model_validate(log) for log in logs],
        "meta": {"limit": limit, "offset": offset},
    }
