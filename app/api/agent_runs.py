"""Agent run REST API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import (
    AgentRunCreate,
    AgentRunOut,
    ApiResponse,
    ToolCallOut,
)
from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


async def _run_support_agent(run_id: str, input_text: str) -> None:
    """Background task to run the support agent workflow."""
    from app.agents.support_graph import build_support_graph
    from app.core.database import async_session_factory

    graph = build_support_graph()
    compiled = graph.compile()

    try:
        result = await compiled.ainvoke({
            "run_id": run_id,
            "mode": "support_agent",
            "input_text": input_text,
        })

        async with async_session_factory() as session:
            db_result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = db_result.scalar_one_or_none()
            if run:
                if result.get("approval_requests"):
                    run.status = "waiting_for_approval"
                else:
                    run.status = "completed"
                run.intent = result.get("intent")
                run.priority = result.get("priority")
                run.draft_response = result.get("draft_response")
                run.final_output = result.get("final_output")
                run.updated_at = datetime.now(timezone.utc)
                await session.commit()
    except Exception as exc:
        async with async_session_factory() as session:
            db_result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = db_result.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.updated_at = datetime.now(timezone.utc)
                await session.commit()


async def _run_workflow_agent(run_id: str, input_text: str) -> None:
    """Background task to run the workflow automation."""
    from app.agents.workflow_graph import build_workflow_graph
    from app.core.database import async_session_factory

    graph = build_workflow_graph()
    compiled = graph.compile()

    try:
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
                    run.status = "waiting_for_approval"
                else:
                    run.status = "completed"
                    run.final_output = result.get("final_report")
                run.updated_at = datetime.now(timezone.utc)
                await session.commit()
    except Exception as exc:
        async with async_session_factory() as session:
            db_result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = db_result.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.updated_at = datetime.now(timezone.utc)
                await session.commit()


@router.post("/support", response_model=ApiResponse[AgentRunOut], status_code=201)
async def create_support_run(
    body: AgentRunCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(timezone.utc)
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

    return {"data": AgentRunOut.model_validate(run)}


@router.post("/workflow", response_model=ApiResponse[AgentRunOut], status_code=201)
async def create_workflow_run(
    body: AgentRunCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(timezone.utc)
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

    return {"data": AgentRunOut.model_validate(run)}


@router.get("/{run_id}", response_model=ApiResponse[AgentRunOut])
async def get_agent_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return {"data": AgentRunOut.model_validate(run)}


@router.get("/{run_id}/tool-calls", response_model=ApiResponse[list[ToolCallOut]])
async def list_tool_calls(
    run_id: str,
    session: AsyncSession = Depends(get_session),
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
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    run.status = "cancelled"
    run.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(run)
    return {"data": AgentRunOut.model_validate(run)}
