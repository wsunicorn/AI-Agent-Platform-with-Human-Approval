"""Ticket REST API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import ApiResponse, TicketCreate, TicketOut, TicketUpdate
from app.models.ticket import Ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=ApiResponse[TicketOut], status_code=201)
async def create_ticket(
    body: TicketCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid4(),
        subject=body.subject,
        body=body.body,
        status="new",
        priority="normal",
        customer_email=body.customer_email,
        customer_name=body.customer_name,
        channel=body.channel,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return {"data": TicketOut.model_validate(ticket)}


@router.get("", response_model=ApiResponse[list[TicketOut]])
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> dict:
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    tickets = result.scalars().all()
    return {
        "data": [TicketOut.model_validate(t) for t in tickets],
        "meta": {"limit": limit, "offset": offset},
    }


@router.get("/{ticket_id}", response_model=ApiResponse[TicketOut])
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"data": TicketOut.model_validate(ticket)}


@router.patch("/{ticket_id}", response_model=ApiResponse[TicketOut])
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(ticket)
    return {"data": TicketOut.model_validate(ticket)}
