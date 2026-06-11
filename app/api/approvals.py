"""Approval REST API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.dependencies import SessionDep
from app.api.schemas import (
    ApiResponse,
    ApprovalAction,
    ApprovalEditAction,
    ApprovalOut,
)
from app.models.approval_request import ApprovalRequest
from app.services.agent_run_summary import refresh_agent_run_summary
from app.services.approval import ApprovalService, ApprovalStateError
from app.tools.executor import ToolExecutor

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _parse_approval_id(approval_id: str) -> UUID:
    try:
        return UUID(approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid approval id") from exc


def _state_error(exc: ApprovalStateError) -> HTTPException:
    status_code = 404 if "not found" in str(exc).lower() else 400
    return HTTPException(status_code=status_code, detail=str(exc))


@router.get("", response_model=ApiResponse[list[ApprovalOut]])
async def list_approvals(
    session: SessionDep,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    query = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
    if status:
        query = query.where(ApprovalRequest.status == status)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    approvals = result.scalars().all()
    return {
        "data": [ApprovalOut.model_validate(a) for a in approvals],
        "meta": {"limit": limit, "offset": offset},
    }


@router.get("/{approval_id}", response_model=ApiResponse[ApprovalOut])
async def get_approval(
    approval_id: str,
    session: SessionDep,
) -> dict:
    approval_uuid = _parse_approval_id(approval_id)
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/approve", response_model=ApiResponse[ApprovalOut])
async def approve(
    approval_id: str,
    body: ApprovalAction,
    session: SessionDep,
) -> dict:
    service = ApprovalService(session)
    try:
        approval = await service.approve(
            approval_id=_parse_approval_id(approval_id),
            reviewer_id=body.reviewer,
            reviewer_comment=body.reason,
        )
    except ApprovalStateError as exc:
        raise _state_error(exc) from exc

    await refresh_agent_run_summary(session, approval.agent_run_id)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/reject", response_model=ApiResponse[ApprovalOut])
async def reject(
    approval_id: str,
    body: ApprovalAction,
    session: SessionDep,
) -> dict:
    service = ApprovalService(session)
    try:
        approval = await service.reject(
            approval_id=_parse_approval_id(approval_id),
            reviewer_id=body.reviewer,
            reviewer_comment=body.reason,
        )
    except ApprovalStateError as exc:
        raise _state_error(exc) from exc

    await refresh_agent_run_summary(session, approval.agent_run_id)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/edit", response_model=ApiResponse[ApprovalOut])
async def edit_payload(
    approval_id: str,
    body: ApprovalEditAction,
    session: SessionDep,
) -> dict:
    service = ApprovalService(session)
    try:
        approval = await service.approve(
            approval_id=_parse_approval_id(approval_id),
            reviewer_id=body.reviewer,
            reviewer_comment=body.reason,
            edited_payload=body.edited_payload,
        )
    except ApprovalStateError as exc:
        raise _state_error(exc) from exc

    await refresh_agent_run_summary(session, approval.agent_run_id)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/execute", response_model=ApiResponse[ApprovalOut])
async def execute_approved(
    approval_id: str,
    session: SessionDep,
) -> dict:
    approval_uuid = _parse_approval_id(approval_id)
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in ("approved", "edited"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute from status: {approval.status}",
        )

    executor = ToolExecutor()
    try:
        await executor.execute_approved(
            session=session,
            approval_id=approval_uuid,
            actor_id="human_admin",
        )
        await refresh_agent_run_summary(session, approval.agent_run_id)
        await session.commit()
    except Exception as exc:
        await refresh_agent_run_summary(session, approval.agent_run_id)
        await session.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Execution failed: {exc}",
        ) from exc

    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}
