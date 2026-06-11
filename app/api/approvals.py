"""Approval REST API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import (
    ApiResponse,
    ApprovalAction,
    ApprovalEditAction,
    ApprovalOut,
)
from app.models.approval_request import ApprovalRequest

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApiResponse[list[ApprovalOut]])
async def list_approvals(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
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
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/approve", response_model=ApiResponse[ApprovalOut])
async def approve(
    approval_id: str,
    body: ApprovalAction,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in ("pending_review", "proposed", "edited"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve from status: {approval.status}",
        )

    approval.status = "approved"
    approval.edited_payload = approval.proposed_payload
    approval.reviewer = body.reviewer
    approval.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/reject", response_model=ApiResponse[ApprovalOut])
async def reject(
    approval_id: str,
    body: ApprovalAction,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in ("pending_review", "proposed", "edited"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject from status: {approval.status}",
        )

    approval.status = "rejected"
    approval.reviewer = body.reviewer
    approval.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/edit", response_model=ApiResponse[ApprovalOut])
async def edit_payload(
    approval_id: str,
    body: ApprovalEditAction,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in ("pending_review", "proposed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit from status: {approval.status}",
        )

    approval.status = "edited"
    approval.edited_payload = body.edited_payload
    approval.reviewer = body.reviewer
    approval.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}


@router.post("/{approval_id}/execute", response_model=ApiResponse[ApprovalOut])
async def execute_approved(
    approval_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    import uuid
    from app.tools.executor import ToolExecutor

    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
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
            approval_id=uuid.UUID(approval_id),
            actor_id="human_admin",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Execution failed: {exc}",
        )

    await session.refresh(approval)
    return {"data": ApprovalOut.model_validate(approval)}
