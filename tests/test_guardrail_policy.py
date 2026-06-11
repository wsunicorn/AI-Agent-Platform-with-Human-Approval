from pydantic import BaseModel

from app.guardrails import PolicyAction, PolicyEngine, PolicyReason
from app.models import Sensitivity
from app.tools.registry import ToolDefinition, ToolRegistry


class Payload(BaseModel):
    value: str


class Output(BaseModel):
    ok: bool


def handler(payload: Payload) -> dict[str, bool]:
    return {"ok": bool(payload.value)}


def register_tool(
    registry: ToolRegistry,
    *,
    name: str,
    sensitivity: Sensitivity = Sensitivity.SAFE,
) -> None:
    registry.register(
        ToolDefinition(
            name=name,
            description=f"{name} test tool.",
            input_model=Payload,
            output_model=Output,
            handler=handler,
            sensitivity=sensitivity,
        )
    )


def test_policy_allows_safe_catalog_tool() -> None:
    registry = ToolRegistry()
    register_tool(registry, name="classify_ticket", sensitivity=Sensitivity.BLOCKED)

    decision = PolicyEngine().decide(
        registry=registry,
        tool_name="classify_ticket",
        payload={"value": "refund"},
    )

    assert decision.action == PolicyAction.ALLOW
    assert decision.sensitivity == Sensitivity.SAFE
    assert decision.reason == PolicyReason.ALLOWED_SAFE_TOOL


def test_policy_requests_approval_for_sensitive_catalog_tool() -> None:
    registry = ToolRegistry()
    register_tool(registry, name="send_email", sensitivity=Sensitivity.SAFE)

    decision = PolicyEngine().decide(
        registry=registry,
        tool_name="send_email",
        payload={"value": "message"},
    )

    assert decision.action == PolicyAction.REQUEST_APPROVAL
    assert decision.sensitivity == Sensitivity.APPROVAL_REQUIRED
    assert decision.reason == PolicyReason.APPROVAL_REQUIRED


def test_policy_denies_blocked_catalog_tool() -> None:
    registry = ToolRegistry()
    register_tool(registry, name="delete_customer_record", sensitivity=Sensitivity.SAFE)

    decision = PolicyEngine().decide(
        registry=registry,
        tool_name="delete_customer_record",
        payload={"value": "customer_123"},
    )

    assert decision.action == PolicyAction.DENY
    assert decision.sensitivity == Sensitivity.BLOCKED
    assert decision.reason == PolicyReason.BLOCKED_TOOL


def test_policy_denies_unregistered_tool() -> None:
    decision = PolicyEngine().decide(
        registry=ToolRegistry(),
        tool_name="missing_tool",
        payload={"value": "x"},
    )

    assert decision.action == PolicyAction.DENY
    assert decision.reason == PolicyReason.UNREGISTERED_TOOL


def test_policy_denies_invalid_payload() -> None:
    registry = ToolRegistry()
    register_tool(registry, name="custom_tool", sensitivity=Sensitivity.SAFE)

    decision = PolicyEngine().decide(
        registry=registry,
        tool_name="custom_tool",
        payload={"wrong": "field"},
    )

    assert decision.action == PolicyAction.DENY
    assert decision.reason == PolicyReason.INVALID_PAYLOAD
    assert decision.details["errors"]
