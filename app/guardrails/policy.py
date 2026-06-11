from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.guardrails.catalog import catalog_sensitivity
from app.models import Sensitivity
from app.tools.registry import ToolRegistry


class PolicyAction(StrEnum):
    ALLOW = "allow"
    REQUEST_APPROVAL = "request_approval"
    DENY = "deny"


class PolicyReason(StrEnum):
    ALLOWED_SAFE_TOOL = "allowed_safe_tool"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED_TOOL = "blocked_tool"
    UNREGISTERED_TOOL = "unregistered_tool"
    INVALID_PAYLOAD = "invalid_payload"


class PolicyDecision(BaseModel):
    action: PolicyAction
    tool_name: str
    sensitivity: Sensitivity | None = None
    reason: PolicyReason
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.action == PolicyAction.ALLOW

    @property
    def requires_approval(self) -> bool:
        return self.action == PolicyAction.REQUEST_APPROVAL

    @property
    def denied(self) -> bool:
        return self.action == PolicyAction.DENY


class PolicyEngine:
    def decide(
        self,
        *,
        registry: ToolRegistry,
        tool_name: str,
        payload: dict[str, Any],
    ) -> PolicyDecision:
        definition = registry.maybe_get(tool_name)
        if definition is None:
            return PolicyDecision(
                action=PolicyAction.DENY,
                tool_name=tool_name,
                reason=PolicyReason.UNREGISTERED_TOOL,
                message="Tool is not registered.",
            )

        sensitivity = catalog_sensitivity(tool_name) or definition.sensitivity

        if sensitivity == Sensitivity.BLOCKED:
            return PolicyDecision(
                action=PolicyAction.DENY,
                tool_name=tool_name,
                sensitivity=sensitivity,
                reason=PolicyReason.BLOCKED_TOOL,
                message="Tool is blocked by policy.",
            )

        try:
            definition.validate_input(payload)
        except ValidationError as error:
            return PolicyDecision(
                action=PolicyAction.DENY,
                tool_name=tool_name,
                sensitivity=sensitivity,
                reason=PolicyReason.INVALID_PAYLOAD,
                message="Tool input payload failed validation.",
                details={"errors": error.errors()},
            )

        if sensitivity == Sensitivity.APPROVAL_REQUIRED:
            return PolicyDecision(
                action=PolicyAction.REQUEST_APPROVAL,
                tool_name=tool_name,
                sensitivity=sensitivity,
                reason=PolicyReason.APPROVAL_REQUIRED,
                message="Sensitive action requires human approval.",
            )

        return PolicyDecision(
            action=PolicyAction.ALLOW,
            tool_name=tool_name,
            sensitivity=sensitivity,
            reason=PolicyReason.ALLOWED_SAFE_TOOL,
            message="Tool is safe to execute.",
        )


policy_engine = PolicyEngine()
