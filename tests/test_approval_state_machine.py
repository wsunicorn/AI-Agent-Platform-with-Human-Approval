import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import (
    AgentRun,
    AgentRunStatus,
    ApprovalRequest,
    ApprovalStatus,
    ToolCall,
    ToolCallStatus,
)
from app.services.approval import ApprovalService, ApprovalStateError


@pytest.mark.asyncio
async def test_create_request() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    audit = AsyncMock()
    service = ApprovalService(session, audit=audit)

    agent_run_id = uuid.uuid4()
    tool_call_id = uuid.uuid4()
    tool_name = "send_email"
    proposed_payload = {"to": "user@example.com", "body": "hello"}
    risk_reason = "Send email is a sensitive action"
    actor_id = "test_agent"

    # Setup database model gets
    mock_tool_call = ToolCall(id=tool_call_id, status=ToolCallStatus.PROPOSED)
    mock_agent_run = AgentRun(id=agent_run_id, status=AgentRunStatus.RUNNING)

    def get_side_effect(model_class, ident):
        if model_class == ToolCall and ident == tool_call_id:
            return mock_tool_call
        if model_class == AgentRun and ident == agent_run_id:
            return mock_agent_run
        return None

    session.get.side_effect = get_side_effect

    approval = await service.create_request(
        agent_run_id=agent_run_id,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        proposed_payload=proposed_payload,
        risk_reason=risk_reason,
        actor_id=actor_id,
    )

    assert approval.agent_run_id == agent_run_id
    assert approval.tool_call_id == tool_call_id
    assert approval.tool_name == tool_name
    assert approval.proposed_payload == proposed_payload
    assert approval.status == ApprovalStatus.PENDING_REVIEW

    # Tool call and agent run status should be updated
    assert mock_tool_call.status == ToolCallStatus.WAITING_FOR_APPROVAL
    assert mock_agent_run.status == AgentRunStatus.WAITING_FOR_APPROVAL

    session.add.assert_called_once_with(approval)
    session.flush.assert_called_once()
    audit.record.assert_called_once()


@pytest.mark.asyncio
async def test_approve_without_edit() -> None:
    session = AsyncMock()
    audit = AsyncMock()
    service = ApprovalService(session, audit=audit)

    approval_id = uuid.uuid4()
    mock_approval = ApprovalRequest(
        id=approval_id,
        status=ApprovalStatus.PENDING_REVIEW,
        tool_name="send_email",
        proposed_payload={"to": "user@example.com"},
    )

    with patch.object(service, "get_for_update", AsyncMock(return_value=mock_approval)):
        updated = await service.approve(
            approval_id=approval_id,
            reviewer_id="human_admin",
            reviewer_comment="looks good",
        )

        assert updated.status == ApprovalStatus.APPROVED
        assert updated.reviewer_id == "human_admin"
        assert updated.reviewer_comment == "looks good"
        assert updated.reviewed_at is not None
        session.flush.assert_called_once()
        audit.record.assert_called_once()


@pytest.mark.asyncio
async def test_approve_with_edit() -> None:
    session = AsyncMock()
    audit = AsyncMock()
    service = ApprovalService(session, audit=audit)

    approval_id = uuid.uuid4()
    mock_approval = ApprovalRequest(
        id=approval_id,
        status=ApprovalStatus.PENDING_REVIEW,
        tool_name="send_email",
        proposed_payload={"to": "user@example.com"},
    )

    with patch.object(service, "get_for_update", AsyncMock(return_value=mock_approval)):
        edited_payload = {"to": "other@example.com"}
        updated = await service.approve(
            approval_id=approval_id,
            reviewer_id="human_admin",
            reviewer_comment="edited recipient",
            edited_payload=edited_payload,
        )

        assert updated.status == ApprovalStatus.EDITED
        assert updated.reviewer_id == "human_admin"
        assert updated.edited_payload == edited_payload
        assert service.final_payload(updated) == edited_payload


@pytest.mark.asyncio
async def test_reject() -> None:
    session = AsyncMock()
    audit = AsyncMock()
    service = ApprovalService(session, audit=audit)

    approval_id = uuid.uuid4()
    mock_tool_call = ToolCall(status=ToolCallStatus.WAITING_FOR_APPROVAL)
    mock_approval = ApprovalRequest(
        id=approval_id,
        status=ApprovalStatus.PENDING_REVIEW,
        tool_name="send_email",
        proposed_payload={"to": "user@example.com"},
        tool_call=mock_tool_call,
    )

    with patch.object(service, "get_for_update", AsyncMock(return_value=mock_approval)):
        updated = await service.reject(
            approval_id=approval_id,
            reviewer_id="human_admin",
            reviewer_comment="blocked",
        )

        assert updated.status == ApprovalStatus.REJECTED
        assert mock_tool_call.status == ToolCallStatus.DENIED


@pytest.mark.asyncio
async def test_invalid_state_transitions() -> None:
    session = AsyncMock()
    service = ApprovalService(session)

    approval_id = uuid.uuid4()

    # Rejecting an already executed request should fail
    mock_approval_executed = ApprovalRequest(
        id=approval_id,
        status=ApprovalStatus.EXECUTED,
    )

    with patch.object(service, "get_for_update", AsyncMock(return_value=mock_approval_executed)):
        with pytest.raises(ApprovalStateError):
            await service.reject(approval_id=approval_id, reviewer_id="human_admin")

        with pytest.raises(ApprovalStateError):
            await service.approve(approval_id=approval_id, reviewer_id="human_admin")
