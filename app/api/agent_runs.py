"""Agent run REST API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import SessionDep
from app.api.schemas import (
    AgentRunCreate,
    AgentRunOut,
    ApiResponse,
    ToolCallOut,
)
from app.models import AgentRunStatus
from app.models.agent_run import AgentRun
from app.models.ticket import Ticket
from app.models.tool_call import ToolCall
from app.services.agent_run_summary import (
    build_agent_run_output,
    refresh_agent_run_summary,
)

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


def _agent_run_out(run: AgentRun) -> AgentRunOut:
    final_output = run.final_output if isinstance(run.final_output, dict) else {}
    return AgentRunOut(
        id=run.id,
        ticket_id=run.ticket_id,
        mode=run.mode,
        status=run.status,
        input_text=run.input_text,
        intent=final_output.get("intent"),
        priority=final_output.get("priority"),
        draft_response=final_output.get("draft_response"),
        final_output=final_output or None,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


async def _mark_run_running(run_id: str) -> dict[str, str | None]:
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        run = await session.scalar(select(AgentRun).where(AgentRun.id == run_id))
        if run is None:
            return {}

        run.status = AgentRunStatus.RUNNING
        run.started_at = run.started_at or datetime.now(UTC)
        run.updated_at = datetime.now(UTC)

        ticket_context: dict[str, str | None] = {}
        if run.ticket_id:
            ticket = await session.scalar(select(Ticket).where(Ticket.id == run.ticket_id))
            if ticket:
                ticket_context = {
                    "ticket_subject": ticket.subject,
                    "ticket_customer_email": ticket.customer_email,
                    "ticket_customer_name": ticket.customer_name,
                    "ticket_priority": str(ticket.priority),
                    "ticket_status": str(ticket.status),
                }
        await session.commit()
        return ticket_context


async def _run_support_agent(run_id: str, input_text: str) -> None:
    """Background task to run the support agent workflow."""
    from app.agents.support_graph import build_support_graph
    from app.core.database import async_session_factory

    ticket_context = await _mark_run_running(run_id)
    graph = build_support_graph()
    compiled = graph.compile()

    try:
        result = await compiled.ainvoke(
            {
                "run_id": run_id,
                "mode": "support_agent",
                "input_text": input_text,
                **ticket_context,
            }
        )

        async with async_session_factory() as session:
            run = await session.scalar(select(AgentRun).where(AgentRun.id == run_id))
            if run:
                run.status = (
                    AgentRunStatus.WAITING_FOR_APPROVAL
                    if result.get("approval_requests")
                    else AgentRunStatus.COMPLETED
                )
                output = result.get("final_output")
                if not isinstance(output, dict):
                    output = {
                        "summary": output or "Support agent run finished.",
                    }
                run.final_output = {
                    **output,
                    "intent": result.get("intent"),
                    "priority": result.get("priority"),
                    "entities": result.get("entities", {}),
                    "citations": result.get("citations", []),
                    "draft_response": result.get("draft_response"),
                    "planned_actions": result.get("planned_actions", []),
                    "approval_requests": result.get("approval_requests", []),
                    "blocked_actions": result.get("blocked_actions", []),
                    "errors": result.get("errors", []),
                    "steps_completed": result.get("steps_completed", []),
                }
                run.updated_at = datetime.now(UTC)
                await session.flush()
                await refresh_agent_run_summary(session, run.id)
                await session.commit()
    except Exception as exc:
        async with async_session_factory() as session:
            run = await session.scalar(select(AgentRun).where(AgentRun.id == run_id))
            if run:
                run.status = AgentRunStatus.FAILED
                run.error_message = str(exc)
                run.updated_at = datetime.now(UTC)
                await session.commit()


async def _run_workflow_agent(run_id: str, input_text: str) -> None:
    """Background task to run the workflow automation."""
    from app.agents.workflow_graph import build_workflow_graph
    from app.core.database import async_session_factory

    graph = build_workflow_graph()
    compiled = graph.compile()

    try:
        async with async_session_factory() as session:
            run = await session.scalar(select(AgentRun).where(AgentRun.id == run_id))
            if run:
                run.status = AgentRunStatus.RUNNING
                run.started_at = run.started_at or datetime.now(UTC)
                run.updated_at = datetime.now(UTC)
                await session.commit()

        result = await compiled.ainvoke({
            "run_id": run_id,
            "mode": "workflow_automation",
            "input_text": input_text,
        })

        async with async_session_factory() as session:
            db_result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = db_result.scalar_one_or_none()
            if run:
                if result.get("approval_requests"):
                    run.status = AgentRunStatus.WAITING_FOR_APPROVAL
                else:
                    run.status = AgentRunStatus.COMPLETED
                    run.final_output = {
                        "summary": result.get("final_report"),
                        "final_report": result.get("final_report"),
                        "tool_results": result.get("tool_results", []),
                        "steps_completed": result.get("steps_completed", []),
                    }
                run.updated_at = datetime.now(UTC)
                await session.flush()
                await refresh_agent_run_summary(session, run.id)
                await session.commit()
    except Exception as exc:
        async with async_session_factory() as session:
            db_result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = db_result.scalar_one_or_none()
            if run:
                run.status = AgentRunStatus.FAILED
                run.error_message = str(exc)
                run.updated_at = datetime.now(UTC)
                await session.commit()


@router.post("/support", response_model=ApiResponse[AgentRunOut], status_code=201)
async def create_support_run(
    body: AgentRunCreate,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> dict:
    now = datetime.now(UTC)
    run_id = uuid4()
    run = AgentRun(
        id=run_id,
        ticket_id=body.ticket_id,
        mode="support_agent",
        input_type="ticket",
        status="queued",
        input_text=body.input_text,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(_run_support_agent, str(run_id), body.input_text)

    return {"data": _agent_run_out(run)}


@router.post("/workflow", response_model=ApiResponse[AgentRunOut], status_code=201)
async def create_workflow_run(
    body: AgentRunCreate,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> dict:
    now = datetime.now(UTC)
    run_id = uuid4()
    run = AgentRun(
        id=run_id,
        ticket_id=body.ticket_id,
        mode="workflow_automation",
        input_type="instruction",
        status="queued",
        input_text=body.input_text,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(_run_workflow_agent, str(run_id), body.input_text)

    return {"data": _agent_run_out(run)}


@router.get("/{run_id}", response_model=ApiResponse[AgentRunOut])
async def get_agent_run(
    run_id: str,
    session: SessionDep,
) -> dict:
    result = await session.execute(
        select(AgentRun)
        .where(AgentRun.id == run_id)
        .options(
            selectinload(AgentRun.tool_calls),
            selectinload(AgentRun.approval_requests),
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    if run.tool_calls or run.approval_requests:
        run.final_output = build_agent_run_output(run)
    return {"data": _agent_run_out(run)}


@router.get("/{run_id}/tool-calls", response_model=ApiResponse[list[ToolCallOut]])
async def list_tool_calls(
    run_id: str,
    session: SessionDep,
) -> dict:
    result = await session.execute(
        select(ToolCall)
        .where(ToolCall.agent_run_id == run_id)
        .order_by(ToolCall.created_at)
    )
    calls = result.scalars().all()
    return {"data": [ToolCallOut.model_validate(c) for c in calls]}


@router.post("/{run_id}/cancel", response_model=ApiResponse[AgentRunOut])
async def cancel_agent_run(
    run_id: str,
    session: SessionDep,
) -> dict:
    result = await session.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    run.status = AgentRunStatus.CANCELLED
    run.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(run)
    return {"data": _agent_run_out(run)}
