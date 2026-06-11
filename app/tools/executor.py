import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.serialization import to_jsonable
from app.guardrails import PolicyAction, PolicyDecision, PolicyEngine, policy_engine
from app.models import ActorType, ApprovalStatus, Sensitivity, ToolCall, ToolCallStatus
from app.services.approval import ApprovalService
from app.services.audit import AuditService
from app.services.redis_lock import RedisLock
from app.services.retry import RetryExhaustedError, RetryPolicy
from app.tools.errors import (
    ToolApprovalRequiredError,
    ToolBlockedError,
    ToolExecutionError,
    ToolNotRegisteredError,
)
from app.tools.registry import ToolDefinition, ToolRegistry, tool_registry


class ToolExecutionResult(BaseModel):
    tool_call_id: uuid.UUID
    tool_name: str
    status: ToolCallStatus
    output_payload: dict[str, Any] | None = None
    approval_request_id: uuid.UUID | None = None
    error_message: str | None = None
    retry_count: int = 0


class ToolExecutor:
    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        audit: AuditService | None = None,
        policy: PolicyEngine | None = None,
    ) -> None:
        self.registry = registry or tool_registry
        self.audit = audit
        self.policy = policy or policy_engine
        self.settings = get_settings()

    async def execute(
        self,
        *,
        session: AsyncSession,
        agent_run_id: uuid.UUID,
        tool_name: str,
        payload: dict[str, Any],
        actor_id: str,
        actor_type: ActorType = ActorType.AGENT,
        require_approval: bool = True,
    ) -> ToolExecutionResult:
        audit = self.audit or AuditService(session)
        decision = self.policy.decide(
            registry=self.registry,
            tool_name=tool_name,
            payload=payload,
        )
        definition = self.registry.maybe_get(tool_name)

        if definition is None:
            await audit.record(
                actor_type=actor_type,
                actor_id=actor_id,
                event_type="guardrail.denied",
                entity_type="agent_run",
                entity_id=str(agent_run_id),
                before_state=None,
                after_state=decision.model_dump(mode="json"),
            )
            raise ToolNotRegisteredError(tool_name)

        tool_call = ToolCall(
            agent_run_id=agent_run_id,
            tool_name=definition.name,
            sensitivity=decision.sensitivity or definition.sensitivity,
            input_payload=to_jsonable(payload),
            status=ToolCallStatus.PROPOSED,
            timeout_ms=int(self.timeout_seconds(definition) * 1000),
        )
        session.add(tool_call)
        await session.flush()

        if decision.action == PolicyAction.DENY:
            return await self._deny_tool_call(
                audit=audit,
                tool_call=tool_call,
                actor_type=actor_type,
                actor_id=actor_id,
                decision=decision,
            )

        if decision.action == PolicyAction.REQUEST_APPROVAL and not require_approval:
            tool_call.status = ToolCallStatus.DENIED
            tool_call.error_message = "Direct execution of approval-required tools is blocked."
            await session.flush()
            await audit.record(
                actor_type=actor_type,
                actor_id=actor_id,
                event_type="guardrail.denied",
                entity_type="tool_call",
                entity_id=str(tool_call.id),
                before_state={"status": ToolCallStatus.PROPOSED},
                after_state=self.snapshot(tool_call),
                metadata=decision.model_dump(mode="json"),
            )
            raise ToolApprovalRequiredError(tool_call.error_message)

        if decision.action == PolicyAction.REQUEST_APPROVAL:
            approval_service = ApprovalService(session, audit=audit)
            approval = await approval_service.create_request(
                agent_run_id=agent_run_id,
                tool_call_id=tool_call.id,
                tool_name=definition.name,
                proposed_payload=payload,
                risk_reason=definition.risk_reason or decision.message,
                actor_id=actor_id,
            )
            return ToolExecutionResult(
                tool_call_id=tool_call.id,
                tool_name=definition.name,
                status=tool_call.status,
                approval_request_id=approval.id,
            )

        return await self._execute_tool_call(
            session=session,
            definition=definition,
            tool_call=tool_call,
            payload=payload,
            actor_id=actor_id,
            actor_type=actor_type,
        )

    async def _deny_tool_call(
        self,
        *,
        audit: AuditService,
        tool_call: ToolCall,
        actor_type: ActorType,
        actor_id: str,
        decision: PolicyDecision,
    ) -> ToolExecutionResult:
        tool_call.status = ToolCallStatus.DENIED
        tool_call.error_message = decision.message
        await audit.session.flush()
        await audit.record(
            actor_type=actor_type,
            actor_id=actor_id,
            event_type="guardrail.denied",
            entity_type="tool_call",
            entity_id=str(tool_call.id),
            before_state={"status": ToolCallStatus.PROPOSED},
            after_state=self.snapshot(tool_call),
            metadata=decision.model_dump(mode="json"),
        )

        if decision.sensitivity == Sensitivity.BLOCKED:
            raise ToolBlockedError(decision.message)

        return ToolExecutionResult(
            tool_call_id=tool_call.id,
            tool_name=tool_call.tool_name,
            status=tool_call.status,
            error_message=tool_call.error_message,
        )

    async def execute_approved(
        self,
        *,
        session: AsyncSession,
        approval_id: uuid.UUID,
        actor_id: str = "approval_executor",
    ) -> ToolExecutionResult:
        audit = self.audit or AuditService(session)
        approval_service = ApprovalService(session, audit=audit)

        async with RedisLock(
            f"approval-execution:{approval_id}",
            ttl_seconds=self.settings.approval_execution_lock_ttl_seconds,
        ):
            approval = await approval_service.get_for_update(approval_id)
            if approval.status not in {ApprovalStatus.APPROVED, ApprovalStatus.EDITED}:
                raise ToolExecutionError(f"Approval is not executable: {approval.status}")

            if approval.tool_call is None:
                raise ToolExecutionError("Approval request does not have a tool call.")

            definition = self.registry.get(approval.tool_name)
            payload = approval_service.final_payload(approval)

            try:
                result = await self._execute_tool_call(
                    session=session,
                    definition=definition,
                    tool_call=approval.tool_call,
                    payload=payload,
                    actor_id=actor_id,
                    actor_type=ActorType.SYSTEM,
                )
                if result.status == ToolCallStatus.COMPLETED:
                    await approval_service.mark_executed(approval, actor_id=actor_id)
                else:
                    await approval_service.mark_failed(
                        approval,
                        actor_id=actor_id,
                        error_message=result.error_message or "Approved tool execution failed.",
                    )
                return result
            except Exception as error:
                await approval_service.mark_failed(
                    approval,
                    actor_id=actor_id,
                    error_message=str(error),
                )
                raise

    async def _execute_tool_call(
        self,
        *,
        session: AsyncSession,
        definition: ToolDefinition[Any, Any],
        tool_call: ToolCall,
        payload: dict[str, Any],
        actor_id: str,
        actor_type: ActorType,
    ) -> ToolExecutionResult:
        audit = self.audit or AuditService(session)
        before_state = self.snapshot(tool_call)
        tool_call.status = ToolCallStatus.RUNNING
        tool_call.started_at = datetime.now(UTC)
        tool_call.input_payload = to_jsonable(payload)
        await session.flush()

        await audit.record(
            actor_type=actor_type,
            actor_id=actor_id,
            event_type="tool_call.started",
            entity_type="tool_call",
            entity_id=str(tool_call.id),
            before_state=before_state,
            after_state=self.snapshot(tool_call),
            metadata={"agent_run_id": str(tool_call.agent_run_id)},
        )

        try:
            validated_input = definition.validate_input(payload)
            retry_policy = self.retry_policy(definition)

            async def operation() -> dict[str, Any]:
                raw_output = await definition.call(validated_input)
                validated_output = definition.validate_output(raw_output)
                return validated_output.model_dump(mode="json")

            output_payload, attempts = await retry_policy.run(operation)
            tool_call.status = ToolCallStatus.COMPLETED
            tool_call.output_payload = to_jsonable(output_payload)
            tool_call.retry_count = max(attempts - 1, 0)
            tool_call.completed_at = datetime.now(UTC)
            await session.flush()
            await audit.record(
                actor_type=actor_type,
                actor_id=actor_id,
                event_type="tool_call.completed",
                entity_type="tool_call",
                entity_id=str(tool_call.id),
                before_state=before_state,
                after_state=self.snapshot(tool_call),
                metadata={"attempts": attempts, "agent_run_id": str(tool_call.agent_run_id)},
            )
            return ToolExecutionResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                status=tool_call.status,
                output_payload=tool_call.output_payload,
                retry_count=tool_call.retry_count,
            )
        except RetryExhaustedError as error:
            tool_call.status = ToolCallStatus.FAILED
            tool_call.error_message = str(error.last_error)
            tool_call.retry_count = max(error.attempts - 1, 0)
            tool_call.completed_at = datetime.now(UTC)
            await session.flush()
            await audit.record(
                actor_type=actor_type,
                actor_id=actor_id,
                event_type="tool_call.failed",
                entity_type="tool_call",
                entity_id=str(tool_call.id),
                before_state=before_state,
                after_state=self.snapshot(tool_call),
                metadata={"attempts": error.attempts, "agent_run_id": str(tool_call.agent_run_id)},
            )
            return ToolExecutionResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                status=tool_call.status,
                error_message=tool_call.error_message,
                retry_count=tool_call.retry_count,
            )
        except Exception as error:
            tool_call.status = ToolCallStatus.FAILED
            tool_call.error_message = str(error)
            tool_call.completed_at = datetime.now(UTC)
            await session.flush()
            await audit.record(
                actor_type=actor_type,
                actor_id=actor_id,
                event_type="tool_call.failed",
                entity_type="tool_call",
                entity_id=str(tool_call.id),
                before_state=before_state,
                after_state=self.snapshot(tool_call),
                metadata={"error_type": type(error).__name__, "agent_run_id": str(tool_call.agent_run_id)},
            )
            return ToolExecutionResult(
                tool_call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                status=tool_call.status,
                error_message=tool_call.error_message,
                retry_count=tool_call.retry_count,
            )

    def retry_policy(self, definition: ToolDefinition[Any, Any]) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=definition.max_attempts or self.settings.tool_default_max_attempts,
            timeout_seconds=definition.timeout_seconds
            or self.settings.tool_default_timeout_seconds,
            initial_backoff_seconds=definition.retry_backoff_seconds
            or self.settings.tool_retry_initial_backoff_seconds,
            backoff_multiplier=self.settings.tool_retry_backoff_multiplier,
        )

    def timeout_seconds(self, definition: ToolDefinition[Any, Any]) -> float:
        return definition.timeout_seconds or self.settings.tool_default_timeout_seconds

    def snapshot(self, tool_call: ToolCall) -> dict[str, Any]:
        return to_jsonable(
            {
                "id": tool_call.id,
                "tool_name": tool_call.tool_name,
                "status": tool_call.status,
                "sensitivity": tool_call.sensitivity,
                "retry_count": tool_call.retry_count,
                "error_message": tool_call.error_message,
                "started_at": tool_call.started_at,
                "completed_at": tool_call.completed_at,
            }
        )
