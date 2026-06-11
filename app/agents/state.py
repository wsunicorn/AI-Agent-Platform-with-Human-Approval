"""Agent workflow state definitions."""

from __future__ import annotations

from typing import Any, TypedDict


class SupportAgentState(TypedDict, total=False):
    """State for the support agent workflow."""

    # Identifiers.
    run_id: str
    ticket_id: str
    mode: str  # "support_agent"

    # Input.
    input_text: str

    # Classification outputs.
    intent: str
    intent_confidence: float
    priority: str
    entities: dict[str, Any]

    # Retrieval.
    retrieval_query: str
    retrieved_context: str
    citations: list[dict[str, Any]]

    # Drafts.
    draft_response: str

    # Action planning.
    planned_actions: list[dict[str, Any]]
    safe_actions: list[dict[str, Any]]
    approval_required_actions: list[dict[str, Any]]
    blocked_actions: list[dict[str, Any]]

    # Approval state.
    approval_requests: list[dict[str, Any]]
    approved_actions: list[dict[str, Any]]

    # Execution results.
    tool_results: list[dict[str, Any]]

    # Output.
    final_output: str

    # Errors.
    errors: list[str]

    # Internal tracking.
    current_step: str
    steps_completed: list[str]


class WorkflowAutomationState(TypedDict, total=False):
    """State for the workflow automation mode."""

    # Identifiers.
    run_id: str
    mode: str  # "workflow_automation"

    # Input.
    input_text: str
    instruction: str

    # Plan.
    plan: list[dict[str, Any]]
    plan_validated: bool

    # Retrieval (optional).
    retrieved_context: str
    citations: list[dict[str, Any]]

    # Action classification.
    safe_actions: list[dict[str, Any]]
    approval_required_actions: list[dict[str, Any]]
    blocked_actions: list[dict[str, Any]]

    # Approval state.
    approval_requests: list[dict[str, Any]]
    approved_actions: list[dict[str, Any]]

    # Execution.
    tool_results: list[dict[str, Any]]

    # Output.
    final_report: str

    # Errors.
    errors: list[str]

    # Internal tracking.
    current_step: str
    steps_completed: list[str]
