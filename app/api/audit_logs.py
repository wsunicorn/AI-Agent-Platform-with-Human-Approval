"""Audit log REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import or_, select

from app.api.dependencies import SessionDep
from app.api.schemas import ApiResponse, AuditLogOut
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _tool_label(name: object) -> str:
    if not isinstance(name, str) or not name:
        return "action"
    return name.replace("_", " ").title()


def _audit_tool_name(log: AuditLog) -> str:
    metadata = _as_dict(log.event_metadata)
    after_state = _as_dict(log.after_state)
    return str(metadata.get("tool_name") or after_state.get("tool_name") or "action")


def _audit_message(log: AuditLog) -> str:
    event = log.event_type
    tool_label = _tool_label(_audit_tool_name(log))
    metadata = _as_dict(log.event_metadata)
    after_state = _as_dict(log.after_state)
    output = _as_dict(after_state.get("output_payload"))

    if event in {"approval.created", "approval.requested"}:
        return f"Agent requested human approval for {tool_label}."
    if event == "approval.approved":
        reviewer = metadata.get("reviewer") or after_state.get("reviewer_id") or log.actor_id
        return f"{reviewer} approved {tool_label}; it is ready to execute."
    if event == "approval.edited":
        reviewer = metadata.get("reviewer") or after_state.get("reviewer_id") or log.actor_id
        return f"{reviewer} edited and approved {tool_label}."
    if event == "approval.rejected":
        reviewer = metadata.get("reviewer") or after_state.get("reviewer_id") or log.actor_id
        return f"{reviewer} rejected {tool_label}; no customer-facing action was executed."
    if event == "approval.executed":
        return f"Approved {tool_label} was executed."
    if event == "approval.failed":
        return f"Approved {tool_label} failed during execution."
    if event == "tool_call.started":
        return f"{tool_label} started."
    if event == "tool_call.completed":
        if _audit_tool_name(log) == "send_email":
            to = output.get("to")
            message_id = output.get("provider_message_id")
            target = f" to {to}" if to else ""
            suffix = f" Message id: {message_id}." if message_id else ""
            return f"Email was sent{target}.{suffix}"
        return f"{tool_label} completed successfully."
    if event == "tool_call.failed":
        return f"{tool_label} failed. Review the error details."
    if event == "guardrail.denied":
        return "Guardrail denied a proposed action before execution."
    if event == "ticket.seeded":
        return "Demo ticket was seeded."
    return event.replace("_", " ").replace(".", " ").title()


def _audit_severity(log: AuditLog) -> str:
    event = log.event_type
    if event.endswith(".failed") or event == "guardrail.denied":
        return "error"
    if event.endswith(".rejected"):
        return "warning"
    if event.endswith(".completed") or event.endswith(".executed"):
        return "success"
    return "info"


def _audit_out(log: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        id=log.id,
        actor_type=log.actor_type,
        actor_id=log.actor_id,
        action=log.event_type,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        before_state=log.before_state,
        after_state=log.after_state,
        metadata_=log.event_metadata,
        message=_audit_message(log),
        severity=_audit_severity(log),
        created_at=log.timestamp,
    )


@router.get("", response_model=ApiResponse[list[AuditLogOut]])
async def list_audit_logs(
    session: SessionDep,
    agent_run_id: str | None = None,
    entity_type: str | None = None,
    actor_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if agent_run_id:
        query = query.where(
            or_(
                AuditLog.event_metadata["agent_run_id"].astext == agent_run_id,
                AuditLog.entity_id == agent_run_id,
            )
        )
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)
    if action:
        query = query.where(AuditLog.event_type == action)

    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    logs = result.scalars().all()
    return {
        "data": [_audit_out(log) for log in logs],
        "meta": {"limit": limit, "offset": offset},
    }
