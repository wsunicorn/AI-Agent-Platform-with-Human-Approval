import uuid
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.support_graph import build_support_graph
from app.agents.workflow_graph import build_workflow_graph
from app.llm.provider import LLMResponse
from app.llm.router import TaskPurpose
from app.models import (
    ActorType,
    AgentRun,
    ApprovalRequest,
    ApprovalStatus,
    Sensitivity,
    ToolCall,
    ToolCallStatus,
)
from app.tools.mock_tools import register_mock_tools
from app.tools.executor import ToolExecutor
from app.services.approval import ApprovalService


def setup_mock_session(session: AsyncMock) -> None:
    tool_calls_added = []
    approvals_added = []
    agent_runs = {}

    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    def session_add_side_effect(obj):
        if isinstance(obj, ToolCall):
            tool_calls_added.append(obj)
        elif isinstance(obj, ApprovalRequest):
            approvals_added.append(obj)
        elif isinstance(obj, AgentRun):
            agent_runs[obj.id] = obj
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()

    session.add.side_effect = session_add_side_effect

    async def session_get_side_effect(model_class, ident):
        if model_class == ToolCall:
            for tc in tool_calls_added:
                if tc.id == ident:
                    return tc
        elif model_class == ApprovalRequest:
            for apr in approvals_added:
                if apr.id == ident:
                    return apr
        elif model_class == AgentRun:
            if ident in agent_runs:
                return agent_runs[ident]
            # fallback mock AgentRun
            return AgentRun(id=ident, status="running")
        return None

    session.get.side_effect = session_get_side_effect

    # Mock scalars/execute for updates or list queries
    async def session_scalar_side_effect(query):
        for apr in approvals_added:
            return apr
        return None

    session.scalar.side_effect = session_scalar_side_effect

    async def session_execute_side_effect(query):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = AgentRun(id=uuid.uuid4(), status="running")
        return mock_result

    session.execute.side_effect = session_execute_side_effect


@pytest.fixture(autouse=True)
def setup_tools() -> None:
    """Ensure mock tools are registered in the registry."""
    register_mock_tools()


@pytest.mark.asyncio
async def test_support_workflow_approval_required_flow() -> None:
    # 1. Setup mock session and router
    mock_session = AsyncMock()
    setup_mock_session(mock_session)

    mock_sessionmaker = MagicMock()
    mock_sessionmaker.return_value.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value.__aexit__.return_value = None

    mock_router = AsyncMock()

    # Stub complete_json calls for intent, priority, entities, and actions planning
    async def complete_json_side_effect(request, purpose):
        content = request.messages[0].content
        if purpose == TaskPurpose.CLASSIFICATION:
            if "Determine the priority" in content or "priority" in content:
                return {"priority": "high", "reason": "VIP refund request"}
            else:
                return {"intent": "refund_request", "confidence": 0.95}
        elif purpose == TaskPurpose.EXTRACTION:
            return {
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "order_id": "98765",
                "product": "Beta",
                "issue_type": "refund",
                "dates": [],
                "amounts": [150.0],
            }
        elif purpose == TaskPurpose.ROUTING:
            return {
                "actions": [
                    {
                        "tool_name": "send_email",
                        "payload": {
                            "to": "jane@example.com",
                            "subject": "Refund Request Received",
                            "body": "Your request is under review.",
                        },
                        "reason": "Notify customer",
                    }
                ]
            }
        return {}

    mock_router.complete_json.side_effect = complete_json_side_effect
    mock_router.complete.return_value = LLMResponse(
        content="Draft Response: Jane, we are looking into this.",
        model="gemini",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=100.0,
    )

    run_id = uuid.uuid4()
    ticket_id = uuid.uuid4()

    # Mocks for retrieve_policy_context helpers
    mock_packed = MagicMock()
    mock_packed.context_text = "Policy: refund requires approval."
    mock_packed.citations = []

    # Mock WebSocketManager to track event broadcasts
    with patch("app.agents.nodes.get_model_router", return_value=mock_router), \
         patch("app.core.database.async_session_factory", return_value=mock_sessionmaker), \
         patch("app.retrieval.search.hybrid_search", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.reranker.rerank_results", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.context.pack_context", return_value=mock_packed), \
         patch("app.services.events.get_redis", return_value=AsyncMock()), \
         patch("app.services.websocket_manager.websocket_manager.broadcast", new_callable=AsyncMock) as mock_broadcast:

        # 2. Compile and run graph
        graph = build_support_graph()
        compiled = graph.compile()

        state = {
            "run_id": str(run_id),
            "ticket_id": str(ticket_id),
            "input_text": "I want a refund for Beta #98765",
            "mode": "support_agent",
        }

        result = await compiled.ainvoke(state)

        # 3. Verify graph results
        assert result.get("intent") == "refund_request"
        assert result.get("priority") == "high"
        assert len(result.get("approval_required_actions", [])) == 1
        assert result.get("approval_required_actions")[0]["tool_name"] == "send_email"
        assert len(result.get("approval_requests", [])) == 1

        # Verify that create_approval_requests was called and added records to DB mock
        assert mock_session.add.call_count >= 2  # ToolCall and ApprovalRequest should have been added
        
        # 4. Human Approval & Execution Flow
        # Retrieve the approval request created
        approval_req = None
        tool_call = None
        for call in mock_session.add.call_args_list:
            obj = call[0][0]
            if isinstance(obj, ApprovalRequest):
                approval_req = obj
            elif isinstance(obj, ToolCall):
                tool_call = obj

        assert approval_req is not None
        assert tool_call is not None
        approval_req.tool_call = tool_call
        assert approval_req.tool_name == "send_email"
        assert approval_req.status == ApprovalStatus.PENDING_REVIEW

        # Now simulate approving the request
        service = ApprovalService(mock_session)
        
        # Patch `get_for_update` to return the mock approval request
        with patch.object(service, "get_for_update", AsyncMock(return_value=approval_req)):
            approved_apr = await service.approve(
                approval_id=approval_req.id,
                reviewer_id="human_reviewer",
                reviewer_comment="Approved!",
            )
            assert approved_apr.status == ApprovalStatus.APPROVED

            # Execute the approved action using ToolExecutor
            executor = ToolExecutor()
            # Mock the RedisLock to do nothing (set return_value of __aexit__ to False to allow exceptions to raise if any)
            with patch("app.tools.executor.RedisLock") as mock_lock:
                mock_lock.return_value.__aenter__ = AsyncMock()
                mock_lock.return_value.__aexit__ = AsyncMock(return_value=False)

                exec_result = await executor.execute_approved(
                    session=mock_session,
                    approval_id=approval_req.id,
                    actor_id="human_reviewer",
                )

                assert exec_result.status == ToolCallStatus.COMPLETED
                assert approval_req.status == ApprovalStatus.EXECUTED


@pytest.mark.asyncio
async def test_support_workflow_blocked_action_flow() -> None:
    mock_session = AsyncMock()
    setup_mock_session(mock_session)

    mock_sessionmaker = MagicMock()
    mock_sessionmaker.return_value.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value.__aexit__.return_value = None

    mock_router = AsyncMock()

    async def complete_json_side_effect(request, purpose):
        if purpose == TaskPurpose.CLASSIFICATION:
            return {"intent": "data_request", "confidence": 0.9}
        elif purpose == TaskPurpose.EXTRACTION:
            return {}
        elif purpose == TaskPurpose.ROUTING:
            return {
                "actions": [
                    {
                        "tool_name": "export_report",  # Let's say this is blocked or has a blocked payload
                        "payload": {"format": "xlsx", "title": "Secret report"},
                        "reason": "Exfiltrate database data",
                    }
                ]
            }
        return {}

    mock_router.complete_json.side_effect = complete_json_side_effect
    mock_router.complete.return_value = LLMResponse(
        content="Draft Response: I cannot do that.",
        model="gemini",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=100.0,
    )

    run_id = uuid.uuid4()
    ticket_id = uuid.uuid4()

    # Modify the PolicyEngine to return BLOCKED for export_report with xlsx
    from app.guardrails.policy import PolicyDecision
    from app.guardrails import PolicyAction, PolicyReason

    mock_policy = MagicMock()
    mock_policy.decide.return_value = PolicyDecision(
        action=PolicyAction.DENY,
        tool_name="export_report",
        sensitivity=Sensitivity.BLOCKED,
        reason=PolicyReason.BLOCKED_TOOL,
        message="Exporting report is blocked by company policy.",
    )

    with patch("app.agents.nodes.get_model_router", return_value=mock_router), \
         patch("app.core.database.async_session_factory", return_value=mock_sessionmaker), \
         patch("app.retrieval.search.hybrid_search", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.reranker.rerank_results", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.context.pack_context", return_value=MagicMock(context_text="", citations=[])), \
         patch("app.guardrails.policy.PolicyEngine", return_value=mock_policy), \
         patch("app.services.events.get_redis", return_value=AsyncMock()):

        graph = build_support_graph()
        compiled = graph.compile()

        state = {
            "run_id": str(run_id),
            "ticket_id": str(ticket_id),
            "input_text": "Export all customer data to excel",
            "mode": "support_agent",
        }

        result = await compiled.ainvoke(state)

        # 3. Verify graph results
        assert len(result.get("blocked_actions", [])) == 1
        assert result.get("blocked_actions")[0]["tool_name"] == "export_report"
        # Since it is blocked, it should NOT run or create approvals
        assert len(result.get("approval_required_actions", [])) == 0
        assert len(result.get("tool_results", [])) == 0


@pytest.mark.asyncio
async def test_workflow_automation_safe_actions_flow() -> None:
    mock_session = AsyncMock()
    setup_mock_session(mock_session)

    mock_sessionmaker = MagicMock()
    mock_sessionmaker.return_value.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value.__aexit__.return_value = None

    mock_router = AsyncMock()

    async def complete_json_side_effect(request, purpose):
        if purpose == TaskPurpose.ROUTING:
            return {
                "plan": [
                    {
                        "step": 1,
                        "tool_name": "search_knowledge_base",
                        "payload": {"query": "refund limits", "limit": 2},
                        "description": "Find policy documentation",
                    }
                ]
            }
        return {}

    mock_router.complete_json.side_effect = complete_json_side_effect
    mock_router.complete.return_value = LLMResponse(
        content="Workflow Completed: Retrieved refund rules.",
        model="gemini",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=100.0,
    )

    run_id = uuid.uuid4()

    with patch("app.agents.nodes.get_model_router", return_value=mock_router), \
         patch("app.core.database.async_session_factory", return_value=mock_sessionmaker), \
         patch("app.services.events.get_redis", return_value=AsyncMock()):

        graph = build_workflow_graph()
        compiled = graph.compile()

        state = {
            "run_id": str(run_id),
            "input_text": "Check refund limits",
            "mode": "workflow_automation",
        }

        result = await compiled.ainvoke(state)

        print("DEBUG RESULT:", json.dumps(result, indent=2, default=str))

        # Verify safe tools were executed and final report generated
        assert len(result.get("safe_actions", [])) == 1
        assert result.get("safe_actions")[0]["tool_name"] == "search_knowledge_base"
        assert len(result.get("tool_results", [])) == 1
        assert result.get("tool_results")[0]["tool_name"] == "search_knowledge_base"
        assert "Workflow Completed" in result.get("final_report", "")


@pytest.mark.asyncio
async def test_support_workflow_rejected_action_flow() -> None:
    mock_session = AsyncMock()
    setup_mock_session(mock_session)

    mock_sessionmaker = MagicMock()
    mock_sessionmaker.return_value.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value.__aexit__.return_value = None

    mock_router = AsyncMock()

    async def complete_json_side_effect(request, purpose):
        content = request.messages[0].content
        if purpose == TaskPurpose.CLASSIFICATION:
            if "Determine the priority" in content or "priority" in content:
                return {"priority": "high", "reason": "VIP refund request"}
            else:
                return {"intent": "refund_request", "confidence": 0.95}
        elif purpose == TaskPurpose.EXTRACTION:
            return {
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "order_id": "98765",
                "product": "Beta",
                "issue_type": "refund",
                "dates": [],
                "amounts": [150.0],
            }
        elif purpose == TaskPurpose.ROUTING:
            return {
                "actions": [
                    {
                        "tool_name": "send_email",
                        "payload": {
                            "to": "jane@example.com",
                            "subject": "Refund Request Received",
                            "body": "Your request is under review.",
                        },
                        "reason": "Notify customer",
                    }
                ]
            }
        return {}

    mock_router.complete_json.side_effect = complete_json_side_effect
    mock_router.complete.return_value = LLMResponse(
        content="Draft Response: Jane, we are looking into this.",
        model="gemini",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=100.0,
    )

    run_id = uuid.uuid4()
    ticket_id = uuid.uuid4()

    with patch("app.agents.nodes.get_model_router", return_value=mock_router), \
         patch("app.core.database.async_session_factory", return_value=mock_sessionmaker), \
         patch("app.retrieval.search.hybrid_search", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.reranker.rerank_results", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.context.pack_context", return_value=MagicMock(context_text="", citations=[])), \
         patch("app.services.events.get_redis", return_value=AsyncMock()):

        graph = build_support_graph()
        compiled = graph.compile()

        state = {
            "run_id": str(run_id),
            "ticket_id": str(ticket_id),
            "input_text": "I want a refund for Beta #98765",
            "mode": "support_agent",
        }

        await compiled.ainvoke(state)

        # Retrieve approval request
        approval_req = None
        tool_call = None
        for call in mock_session.add.call_args_list:
            obj = call[0][0]
            if isinstance(obj, ApprovalRequest):
                approval_req = obj
            elif isinstance(obj, ToolCall):
                tool_call = obj

        assert approval_req is not None
        assert tool_call is not None
        approval_req.tool_call = tool_call

        # Simulate Reject
        service = ApprovalService(mock_session)
        with patch.object(service, "get_for_update", AsyncMock(return_value=approval_req)):
            rejected_apr = await service.reject(
                approval_id=approval_req.id,
                reviewer_id="human_reviewer",
                reviewer_comment="Rejection: Not allowed.",
            )
            assert rejected_apr.status == ApprovalStatus.REJECTED
            assert tool_call.status == ToolCallStatus.DENIED

            # Try executing and verify it raises a ToolExecutionError
            executor = ToolExecutor()
            from app.tools.errors import ToolExecutionError
            with patch("app.tools.executor.RedisLock") as mock_lock:
                mock_lock.return_value.__aenter__ = AsyncMock()
                mock_lock.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(ToolExecutionError, match="Approval is not executable"):
                    await executor.execute_approved(
                        session=mock_session,
                        approval_id=approval_req.id,
                        actor_id="human_reviewer",
                    )


@pytest.mark.asyncio
async def test_integration_audit_logging() -> None:
    from app.models import AuditLog
    # 1. Setup mock session and router
    mock_session = AsyncMock()
    setup_mock_session(mock_session)

    mock_sessionmaker = MagicMock()
    mock_sessionmaker.return_value.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value.__aexit__.return_value = None

    mock_router = AsyncMock()
    
    async def complete_json_side_effect(request, purpose):
        if purpose == TaskPurpose.CLASSIFICATION:
            return {"intent": "refund_request", "confidence": 0.95}
        elif purpose == TaskPurpose.EXTRACTION:
            return {"order_id": "123"}
        elif purpose == TaskPurpose.ROUTING:
            return {
                "actions": [
                    {
                        "tool_name": "send_email",
                        "payload": {"to": "jane@example.com", "subject": "Refund", "body": "Ok"},
                        "reason": "Notify customer",
                    }
                ]
            }
        return {}

    mock_router.complete_json.side_effect = complete_json_side_effect
    mock_router.complete.return_value = LLMResponse(
        content="Draft Response",
        model="gemini",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=100.0,
    )

    run_id = uuid.uuid4()
    ticket_id = uuid.uuid4()

    with patch("app.agents.nodes.get_model_router", return_value=mock_router), \
         patch("app.core.database.async_session_factory", return_value=mock_sessionmaker), \
         patch("app.retrieval.search.hybrid_search", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.reranker.rerank_results", new_callable=AsyncMock, return_value=[]), \
         patch("app.retrieval.context.pack_context", return_value=MagicMock(context_text="", citations=[])), \
         patch("app.services.events.get_redis", return_value=AsyncMock()):

        graph = build_support_graph()
        compiled = graph.compile()

        state = {
            "run_id": str(run_id),
            "ticket_id": str(ticket_id),
            "input_text": "I want a refund for order #123",
            "mode": "support_agent",
        }

        await compiled.ainvoke(state)

        # Inspect added items in session to find AuditLog records
        audit_logs = []
        for call in mock_session.add.call_args_list:
            obj = call[0][0]
            if isinstance(obj, AuditLog):
                audit_logs.append(obj)

        assert len(audit_logs) > 0
        event_types = [log.event_type for log in audit_logs]
        assert "approval.created" in event_types


@pytest.mark.asyncio
async def test_websocket_event_delivery() -> None:
    import asyncio
    from app.api.websockets import _agent_run_manager, _approval_manager, redis_event_listener
    from starlette.websockets import WebSocketState
    
    # Let's mock the WebSocket objects
    mock_ws_run = AsyncMock()
    mock_ws_run.client_state = WebSocketState.CONNECTED
    
    mock_ws_approval = AsyncMock()
    mock_ws_approval.client_state = WebSocketState.CONNECTED
    
    run_id = "test-run-id-123"
    
    # Connect them to our managers
    await _agent_run_manager.connect(mock_ws_run, topic=run_id)
    await _approval_manager.connect(mock_ws_approval, topic="approvals")
    
    # Prepare a mock Redis pubsub message containing an EventEnvelope
    envelope_data = {
        "id": "event-123",
        "event_type": "audit_log.created",
        "entity_type": "audit_log",
        "entity_id": "audit-log-123",
        "payload": {
            "event_type": "approval.created",
            "entity_type": "approval_request",
            "entity_id": "approval-req-123",
            "metadata": {
                "agent_run_id": run_id,
                "tool_name": "send_email",
            }
        },
        "created_at": "2026-06-11T12:00:00Z"
    }
    
    mock_redis = MagicMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub
    
    messages = [
        {"type": "message", "data": json.dumps(envelope_data)},
        None
    ]
    
    async def get_message_side_effect(*args, **kwargs):
        if messages:
            return messages.pop(0)
        raise asyncio.CancelledError()
        
    mock_pubsub.get_message.side_effect = get_message_side_effect
    
    with patch("app.api.websockets.get_redis", return_value=mock_redis), \
         patch("app.api.websockets.get_settings") as mock_settings:
         
        mock_settings.return_value.redis_events_channel = "humangate.events"
        
        try:
            await redis_event_listener()
        except asyncio.CancelledError:
            pass
            
        assert mock_ws_run.send_json.call_count == 1
        call_args = mock_ws_run.send_json.call_args[0][0]
        assert call_args["type"] == "approval.created"
        assert call_args["data"]["agent_run_id"] == run_id
        
        assert mock_ws_approval.send_json.call_count == 1
        
    # Clean up connections
    _agent_run_manager.disconnect(mock_ws_run, topic=run_id)
    _approval_manager.disconnect(mock_ws_approval, topic="approvals")
