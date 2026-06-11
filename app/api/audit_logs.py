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
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if agent_run_id:
        query = query.where(AuditLog.agent_run_id == agent_run_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)
    if action:
        query = query.where(AuditLog.action == action)

    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    logs = result.scalars().all()
    return {
        "data": [AuditLogOut.model_validate(log) for log in logs],
        "meta": {"limit": limit, "offset": offset},
    }
