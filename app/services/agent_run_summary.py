"""Helpers for turning durable run records into operator-readable status."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.serialization import to_jsonable
from app.models import (
    AgentRun,
    AgentRunStatus,
    ApprovalRequest,
    ApprovalStatus,
    TicketStatus,
    ToolCall,
    ToolCallStatus,
)
from app.models.ticket import Ticket

WAITING_APPROVAL_STATUSES = {
    ApprovalStatus.PROPOSED,
    ApprovalStatus.PENDING_REVIEW,
    ApprovalStatus.APPROVED,
    ApprovalStatus.EDITED,
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _status_value(value: Any) -> str:
    return getattr(value, "value", str(value))


def _tool_label(tool_name: str) -> str:
    return tool_name.replace("_", " ").title()


def _find_draft_response(run: AgentRun, tool_calls: list[ToolCall]) -> str | None:
    existing = _as_dict(run.final_output)
    draft = existing.get("draft_response")
    if isinstance(draft, str) and draft:
        return draft

    for call in tool_calls:
        if call.tool_name != "draft_email_response":
            continue
        output = _as_dict(call.output_payload)
        for key in ("body", "draft"):
            value = output.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def summarize_tool_call(call: ToolCall) -> dict[str, Any]:
    """Create a compact, user-facing summary for one tool call."""
    input_payload = _as_dict(call.input_payload)
    output_payload = _as_dict(call.output_payload)
    status = _status_value(call.status)

    summary: dict[str, Any] = {
        "id": str(call.id),
        "tool_name": call.tool_name,
        "label": _tool_label(call.tool_name),
        "status": status,
        "sensitivity": _status_value(call.sensitivity),
        "completed_at": call.completed_at,
        "error_message": call.error_message,
    }

    if call.tool_name == "send_email":
        summary.update(
            {
                "kind": "email",
                "to": output_payload.get("to") or input_payload.get("to"),
                "subject": output_payload.get("subject") or input_payload.get("subject"),
                "body": input_payload.get("body"),
                "delivery_status": output_payload.get("status")
                or ("pending_review" if status == "waiting_for_approval" else status),
                "provider": output_payload.get("provider"),
                "provider_message_id": output_payload.get("provider_message_id"),
                "sent_at": output_payload.get("sent_at"),
            }
        )
    elif call.tool_name == "create_crm_note":
        summary.update(
            {
                "kind": "crm_note",
                "summary": output_payload.get("summary") or input_payload.get("note"),
                "crm_note_id": output_payload.get("crm_note_id"),
            }
        )
    elif call.tool_name == "export_report":
        summary.update(
            {
                "kind": "report_export",
                "title": input_payload.get("title"),
                "format": output_payload.get("format") or input_payload.get("format"),
                "download_url": output_payload.get("download_url"),
            }
        )
    else:
        summary.update(
            {
                "kind": "tool",
                "summary": output_payload.get("summary")
                or output_payload.get("rationale")
                or output_payload.get("status"),
            }
        )

    return to_jsonable(summary)


def summarize_approval(approval: ApprovalRequest) -> dict[str, Any]:
    return to_jsonable(
        {
            "id": str(approval.id),
            "tool_name": approval.tool_name,
            "status": _status_value(approval.status),
            "reviewer": approval.reviewer_id,
            "reviewer_comment": approval.reviewer_comment,
            "reviewed_at": approval.reviewed_at,
            "executed_at": approval.executed_at,
            "risk_reason": approval.risk_reason,
        }
    )


def derive_agent_run_status(run: AgentRun) -> AgentRunStatus:
    approvals = list(run.approval_requests)
    tool_calls = list(run.tool_calls)

    if run.status == AgentRunStatus.CANCELLED:
        return AgentRunStatus.CANCELLED
    if any(call.status == ToolCallStatus.RUNNING for call in tool_calls):
        return AgentRunStatus.RUNNING
    if any(approval.status in WAITING_APPROVAL_STATUSES for approval in approvals):
        return AgentRunStatus.WAITING_FOR_APPROVAL
    if any(call.status == ToolCallStatus.FAILED for call in tool_calls) or any(
        approval.status == ApprovalStatus.FAILED for approval in approvals
    ):
        return AgentRunStatus.FAILED
    return AgentRunStatus.COMPLETED


def build_agent_run_output(run: AgentRun) -> dict[str, Any]:
    """Build the structured final output shown in the dashboard."""
    existing = _as_dict(run.final_output)
    tool_calls = list(run.tool_calls)
    approvals = list(run.approval_requests)
    actions = [summarize_tool_call(call) for call in tool_calls]
    approvals_summary = [summarize_approval(approval) for approval in approvals]

    deliveries = [
        action
        for action in actions
        if action.get("kind") in {"email", "crm_note", "report_export"}
        and action.get("status") == ToolCallStatus.COMPLETED.value
    ]
    pending_approvals = [
        approval
        for approval in approvals_summary
        if approval.get("status") in {status.value for status in WAITING_APPROVAL_STATUSES}
    ]
    rejected_approvals = [
        approval
        for approval in approvals_summary
        if approval.get("status") == ApprovalStatus.REJECTED.value
    ]
    failed_actions = [
        action
        for action in actions
        if action.get("status") in {ToolCallStatus.FAILED.value, ToolCallStatus.DENIED.value}
    ]

    if pending_approvals:
        summary = "Waiting for human review or execution of approved sensitive actions."
    elif deliveries:
        delivery_labels = ", ".join(delivery["label"] for delivery in deliveries)
        summary = f"Completed approved delivery actions: {delivery_labels}."
    elif rejected_approvals:
        summary = "Reviewer rejected the sensitive action; no outbound action was executed."
    elif failed_actions:
        summary = "Some actions failed or were denied. Review the action details."
    else:
        completed_count = len(
            [action for action in actions if action.get("status") == ToolCallStatus.COMPLETED.value]
        )
        summary = (
            f"Completed {completed_count} safe action(s)."
            if completed_count
            else "The run finished without executing any tools."
        )

    output = {
        **existing,
        "summary": summary,
        "status": _status_value(run.status),
        "draft_response": _find_draft_response(run, tool_calls),
        "actions": actions,
        "deliveries": deliveries,
        "approvals": approvals_summary,
        "counts": {
            "tool_calls": len(tool_calls),
            "completed_actions": len(
                [
                    action
                    for action in actions
                    if action.get("status") == ToolCallStatus.COMPLETED.value
                ]
            ),
            "pending_approvals": len(pending_approvals),
            "rejected_approvals": len(rejected_approvals),
            "failed_actions": len(failed_actions),
            "deliveries": len(deliveries),
        },
    }
    return to_jsonable(output)


def ticket_status_for_run(
    status: AgentRunStatus, output: dict[str, Any] | None = None
) -> TicketStatus:
    if status == AgentRunStatus.WAITING_FOR_APPROVAL:
        return TicketStatus.WAITING_FOR_APPROVAL
    if status == AgentRunStatus.COMPLETED:
        counts = _as_dict((output or {}).get("counts"))
        # A run where the only outcome was a human rejecting the sensitive
        # action (no successful deliveries) still resolves as COMPLETED, but
        # it should not read the same as a genuinely fulfilled ticket.
        if counts.get("rejected_approvals") and not counts.get("deliveries"):
            return TicketStatus.IN_PROGRESS
        return TicketStatus.RESOLVED
    if status == AgentRunStatus.CANCELLED:
        return TicketStatus.TRIAGED
    return TicketStatus.IN_PROGRESS


def _first_text(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


async def sync_ticket_from_run(
    session: AsyncSession,
    run: AgentRun,
    status: AgentRunStatus,
    output: dict[str, Any],
) -> None:
    if run.ticket_id is None:
        return

    ticket = await session.get(Ticket, run.ticket_id)
    if ticket is None:
        return

    ticket.status = ticket_status_for_run(status, output)
    ticket.intent = _first_text(output.get("intent")) or ticket.intent
    ticket.priority = _first_text(output.get("priority")) or ticket.priority
    entities = output.get("entities")
    if isinstance(entities, dict):
        ticket.extracted_entities = entities
        issue_type = _first_text(entities.get("issue_type"))
        if issue_type:
            ticket.issue_type = issue_type
    ticket.updated_at = datetime.now(UTC)


async def refresh_agent_run_summary(
    session: AsyncSession,
    run_id: uuid.UUID,
) -> AgentRun | None:
    """Refresh run status/output from persisted tool calls and approvals."""
    run = await session.scalar(
        select(AgentRun)
        .where(AgentRun.id == run_id)
        .options(
            selectinload(AgentRun.tool_calls),
            selectinload(AgentRun.approval_requests),
        )
    )
    if run is None:
        return None

    status = derive_agent_run_status(run)
    output = build_agent_run_output(run)
    run.status = status
    run.final_output = output
    run.updated_at = datetime.now(UTC)
    if status in {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }:
        run.completed_at = run.completed_at or datetime.now(UTC)
    await sync_ticket_from_run(session, run, status, output)
    await session.flush()
    return run
