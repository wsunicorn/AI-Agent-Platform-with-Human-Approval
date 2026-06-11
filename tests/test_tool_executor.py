import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.guardrails import PolicyAction, PolicyDecision, PolicyEngine, PolicyReason
from app.models import ActorType, AgentRun, ApprovalRequest, ApprovalStatus, Sensitivity, ToolCall, ToolCallStatus
from app.tools.errors import ToolApprovalRequiredError, ToolBlockedError, ToolNotRegisteredError
from app.tools.executor import ToolExecutor, ToolExecutionResult
from app.tools.registry import ToolDefinition, ToolRegistry


def setup_mock_session(session: AsyncMock) -> None:
    tool_calls_added = []

    # session.add is synchronous in SQLAlchemy, so we use MagicMock instead of AsyncMock.
    session.add = MagicMock()

    def session_add_side_effect(obj):
        if isinstance(obj, ToolCall):
            tool_calls_added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
    session.add.side_effect = session_add_side_effect

    async def session_get_side_effect(model_class, ident):
        if model_class == ToolCall:
            for tc in tool_calls_added:
                if tc.id == ident:
                    return tc
        if model_class == AgentRun:
            return AgentRun(id=ident, status="running")
        return None
    session.get.side_effect = session_get_side_effect


@pytest.mark.asyncio
async def test_execute_unregistered_tool() -> None:
    session = AsyncMock()
    setup_mock_session(session)
    audit = AsyncMock()
    policy = MagicMock()

    # Setup policy engine to return unregistered tool decision
    policy.decide.return_value = PolicyDecision(
        action=PolicyAction.DENY,
        tool_name="unknown_tool",
        sensitivity=None,
        reason=PolicyReason.UNREGISTERED_TOOL,
        message="Tool not registered",
    )

    registry = ToolRegistry()
    executor = ToolExecutor(registry=registry, audit=audit, policy=policy)

    agent_run_id = uuid.uuid4()

    with pytest.raises(ToolNotRegisteredError):
        await executor.execute(
            session=session,
            agent_run_id=agent_run_id,
            tool_name="unknown_tool",
            payload={},
            actor_id="test_agent",
        )

    audit.record.assert_called_once()


@pytest.mark.asyncio
async def test_execute_blocked_tool() -> None:
    session = AsyncMock()
    setup_mock_session(session)
    audit = AsyncMock()
    policy = MagicMock()

    # Mock tool definition
    mock_definition = MagicMock(spec=ToolDefinition)
    mock_definition.name = "delete_db"
    mock_definition.sensitivity = Sensitivity.BLOCKED
    mock_definition.timeout_seconds = 10.0

    registry = ToolRegistry()
    registry.register(mock_definition)

    policy.decide.return_value = PolicyDecision(
        action=PolicyAction.DENY,
        tool_name="delete_db",
        sensitivity=Sensitivity.BLOCKED,
        reason=PolicyReason.BLOCKED_TOOL,
        message="This tool is blocked",
    )

    executor = ToolExecutor(registry=registry, audit=audit, policy=policy)
    agent_run_id = uuid.uuid4()

    with patch("app.tools.executor.ToolCall", side_effect=lambda *a, **k: ToolCall(*a, id=k.pop("id", uuid.uuid4()), **k)):
        with pytest.raises(ToolBlockedError):
            await executor.execute(
                session=session,
                agent_run_id=agent_run_id,
                tool_name="delete_db",
                payload={},
                actor_id="test_agent",
            )

    session.add.assert_called_once()
    audit.record.assert_called_once()


@pytest.mark.asyncio
async def test_execute_approval_required_tool() -> None:
    session = AsyncMock()
    setup_mock_session(session)
    audit = AsyncMock()
    policy = MagicMock()

    mock_definition = MagicMock(spec=ToolDefinition)
    mock_definition.name = "send_email"
    mock_definition.sensitivity = Sensitivity.APPROVAL_REQUIRED
    mock_definition.timeout_seconds = 5.0
    mock_definition.risk_reason = "Send email"

    registry = ToolRegistry()
    registry.register(mock_definition)

    policy.decide.return_value = PolicyDecision(
        action=PolicyAction.REQUEST_APPROVAL,
        tool_name="send_email",
        sensitivity=Sensitivity.APPROVAL_REQUIRED,
        reason=PolicyReason.APPROVAL_REQUIRED,
        message="Approval required for send_email",
    )

    executor = ToolExecutor(registry=registry, audit=audit, policy=policy)
    agent_run_id = uuid.uuid4()

    with patch("app.tools.executor.ToolCall", side_effect=lambda *a, **k: ToolCall(*a, id=k.pop("id", uuid.uuid4()), **k)):
        result = await executor.execute(
            session=session,
            agent_run_id=agent_run_id,
            tool_name="send_email",
            payload={"to": "customer@example.com"},
            actor_id="test_agent",
        )

        assert result.status == ToolCallStatus.WAITING_FOR_APPROVAL
        assert result.approval_request_id is not None
        audit.record.assert_called_once()
