import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.serialization import to_jsonable
from app.models import (
    ActorType,
    AgentRun,
    AgentRunStatus,
    ApprovalRequest,
    ApprovalStatus,
    ToolCall,
    ToolCallStatus,
)
from app.services.audit import AuditService


class ApprovalStateError(RuntimeError):
    pass


class ApprovalService:
    def __init__(self, session: AsyncSession, audit: AuditService | None = None) -> None:
        self.session = session
        self.audit = audit or AuditService(session)

    async def create_request(
        self,
        *,
        agent_run_id: uuid.UUID,
        tool_call_id: uuid.UUID,
        tool_name: str,
        proposed_payload: dict[str, Any],
        risk_reason: str,
        actor_id: str,
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            agent_run_id=agent_run_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            proposed_payload=to_jsonable(proposed_payload),
            risk_reason=risk_reason,
            status=ApprovalStatus.PENDING_REVIEW,
        )
        self.session.add(approval)

        tool_call = await self.session.get(ToolCall, tool_call_id)
        if tool_call is not None:
            tool_call.status = ToolCallStatus.WAITING_FOR_APPROVAL

        agent_run = await self.session.get(AgentRun, agent_run_id)
        if agent_run is not None:
            agent_run.status = AgentRunStatus.WAITING_FOR_APPROVAL

        await self.session.flush()
        await self.audit.record(
            actor_type=ActorType.AGENT,
            actor_id=actor_id,
            event_type="approval.created",
            entity_type="approval_request",
            entity_id=str(approval.id),
            before_state=None,
            after_state={
                "status": approval.status,
                "tool_name": approval.tool_name,
                "agent_run_id": str(agent_run_id),
                "tool_call_id": str(tool_call_id),
            },
            metadata={
                "agent_run_id": str(agent_run_id),
                "tool_call_id": str(tool_call_id),
                "tool_name": tool_name,
                "risk_reason": risk_reason,
            },
        )
        return approval

    async def get_for_update(self, approval_id: uuid.UUID) -> ApprovalRequest:
        approval = await self.session.scalar(
            select(ApprovalRequest)
            .where(ApprovalRequest.id == approval_id)
            .options(selectinload(ApprovalRequest.tool_call))
            .with_for_update()
        )
        if approval is None:
            raise ApprovalStateError(f"Approval request not found: {approval_id}")
        return approval

    async def approve(
        self,
        *,
        approval_id: uuid.UUID,
        reviewer_id: str,
        reviewer_comment: str | None = None,
        edited_payload: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        approval = await self.get_for_update(approval_id)
        if approval.status not in {
            ApprovalStatus.PENDING_REVIEW,
            ApprovalStatus.PROPOSED,
            ApprovalStatus.EDITED,
        }:
            raise ApprovalStateError(f"Cannot approve request in state: {approval.status}")

        before_state = self.snapshot(approval)
        approval.reviewer_id = reviewer_id
        approval.reviewer_comment = reviewer_comment
        approval.reviewed_at = datetime.now(UTC)

        if edited_payload is not None:
            approval.edited_payload = to_jsonable(edited_payload)
            approval.status = ApprovalStatus.EDITED
            event_type = "approval.edited"
        else:
            approval.status = ApprovalStatus.APPROVED
            event_type = "approval.approved"

        await self.session.flush()
        await self.audit.record(
            actor_type=ActorType.HUMAN,
            actor_id=reviewer_id,
            event_type=event_type,
            entity_type="approval_request",
            entity_id=str(approval.id),
            before_state=before_state,
            after_state=self.snapshot(approval),
            metadata={
                "agent_run_id": str(approval.agent_run_id),
                "tool_call_id": str(approval.tool_call_id),
                "tool_name": approval.tool_name,
                "reviewer_comment": reviewer_comment,
            },
        )
        return approval

    async def reject(
        self,
        *,
        approval_id: uuid.UUID,
        reviewer_id: str,
        reviewer_comment: str | None = None,
    ) -> ApprovalRequest:
        approval = await self.get_for_update(approval_id)
        if approval.status not in {
            ApprovalStatus.PENDING_REVIEW,
            ApprovalStatus.PROPOSED,
            ApprovalStatus.APPROVED,
            ApprovalStatus.EDITED,
        }:
            raise ApprovalStateError(f"Cannot reject request in state: {approval.status}")

        before_state = self.snapshot(approval)
        approval.status = ApprovalStatus.REJECTED
        approval.reviewer_id = reviewer_id
        approval.reviewer_comment = reviewer_comment
        approval.reviewed_at = datetime.now(UTC)

        if approval.tool_call is not None:
            approval.tool_call.status = ToolCallStatus.DENIED

        await self.session.flush()
        await self.audit.record(
            actor_type=ActorType.HUMAN,
            actor_id=reviewer_id,
            event_type="approval.rejected",
            entity_type="approval_request",
            entity_id=str(approval.id),
            before_state=before_state,
            after_state=self.snapshot(approval),
            metadata={
                "agent_run_id": str(approval.agent_run_id),
                "tool_call_id": str(approval.tool_call_id),
                "tool_name": approval.tool_name,
                "reviewer_comment": reviewer_comment,
            },
        )
        return approval

    async def mark_executed(self, approval: ApprovalRequest, actor_id: str) -> None:
        if approval.status not in {ApprovalStatus.APPROVED, ApprovalStatus.EDITED}:
            raise ApprovalStateError(f"Cannot execute request in state: {approval.status}")

        before_state = self.snapshot(approval)
        approval.status = ApprovalStatus.EXECUTED
        approval.executed_at = datetime.now(UTC)
        await self.session.flush()
        await self.audit.record(
            actor_type=ActorType.SYSTEM,
            actor_id=actor_id,
            event_type="approval.executed",
            entity_type="approval_request",
            entity_id=str(approval.id),
            before_state=before_state,
            after_state=self.snapshot(approval),
            metadata={
                "agent_run_id": str(approval.agent_run_id),
                "tool_call_id": str(approval.tool_call_id),
                "tool_name": approval.tool_name,
            },
        )

    async def mark_failed(
        self,
        approval: ApprovalRequest,
        *,
        actor_id: str,
        error_message: str,
    ) -> None:
        before_state = self.snapshot(approval)
        approval.status = ApprovalStatus.FAILED
        await self.session.flush()
        await self.audit.record(
            actor_type=ActorType.SYSTEM,
            actor_id=actor_id,
            event_type="approval.failed",
            entity_type="approval_request",
            entity_id=str(approval.id),
            before_state=before_state,
            after_state=self.snapshot(approval),
            metadata={
                "agent_run_id": str(approval.agent_run_id),
                "tool_call_id": str(approval.tool_call_id),
                "tool_name": approval.tool_name,
                "error_message": error_message,
            },
        )

    def final_payload(self, approval: ApprovalRequest) -> dict[str, Any]:
        return approval.edited_payload or approval.proposed_payload

    def snapshot(self, approval: ApprovalRequest) -> dict[str, Any]:
        return to_jsonable(
            {
                "id": approval.id,
                "status": approval.status,
                "tool_name": approval.tool_name,
                "reviewer_id": approval.reviewer_id,
                "reviewed_at": approval.reviewed_at,
                "executed_at": approval.executed_at,
                "agent_run_id": approval.agent_run_id,
                "tool_call_id": approval.tool_call_id,
            }
        )
