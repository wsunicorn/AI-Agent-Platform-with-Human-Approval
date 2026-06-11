"""Pydantic schemas for all API request/response types."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Standard API Envelope ────────────────────────────────────────────


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiMeta(BaseModel):
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ApiError | None = None
    meta: ApiMeta | None = None


# ── Ticket Schemas ───────────────────────────────────────────────────


class TicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    customer_email: str | None = None
    customer_name: str | None = None
    channel: str = "web"


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None


class TicketOut(BaseModel):
    id: UUID
    subject: str
    body: str
    status: str
    priority: str
    intent: str | None = None
    customer_email: str | None = None
    customer_name: str | None = None
    channel: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Run Schemas ────────────────────────────────────────────────


class AgentRunCreate(BaseModel):
    ticket_id: UUID | None = None
    input_text: str = Field(min_length=1)


class AgentRunOut(BaseModel):
    id: UUID
    ticket_id: UUID | None = None
    mode: str
    status: str
    input_text: str
    intent: str | None = None
    priority: str | None = None
    draft_response: str | None = None
    final_output: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Tool Call Schemas ────────────────────────────────────────────────


class ToolCallOut(BaseModel):
    id: UUID
    agent_run_id: UUID
    tool_name: str
    status: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] | None = None
    error_message: str | None = None
    sensitivity: str | None = None
    duration_ms: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Approval Schemas ─────────────────────────────────────────────────


class ApprovalOut(BaseModel):
    id: UUID
    agent_run_id: UUID
    tool_call_id: UUID | None = None
    tool_name: str
    status: str
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    edited_payload: dict[str, Any] | None = None
    risk_reason: str | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    reviewer: str = "admin"
    reason: str | None = None


class ApprovalEditAction(BaseModel):
    reviewer: str = "admin"
    edited_payload: dict[str, Any]
    reason: str | None = None


# ── Knowledge Base Schemas ───────────────────────────────────────────


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    doc_type: str = "policy"
    tags: list[str] = Field(default_factory=list)
    source_url: str | None = None


class KnowledgeDocumentOut(BaseModel):
    id: UUID
    title: str
    doc_type: str
    status: str
    tags: list[str]
    source_url: str | None = None
    chunk_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    doc_type: str | None = None
    limit: int = 10


class KnowledgeSearchResult(BaseModel):
    chunk_content: str
    score: float
    method: str
    document_title: str | None = None
    heading: str | None = None


# ── Audit Log Schemas ────────────────────────────────────────────────


class AuditLogOut(BaseModel):
    id: UUID
    actor_type: str
    actor_id: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    metadata_: dict[str, Any] | None = Field(None, serialization_alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Settings Schemas ─────────────────────────────────────────────────


class ModelConfigOut(BaseModel):
    id: UUID
    provider: str
    model_name: str
    purpose: str
    mode: str
    is_default: bool
    is_enabled: bool
    config: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class ModelConfigCreate(BaseModel):
    provider: str
    model_name: str
    purpose: str = "default"
    mode: str = "hosted"
    is_default: bool = False
    is_enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ModelConfigUpdate(BaseModel):
    is_default: bool | None = None
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None


class ToolConfigOut(BaseModel):
    name: str
    sensitivity: str
    description: str | None = None
    enabled: bool = True


class ToolConfigUpdate(BaseModel):
    sensitivity: str | None = None
    enabled: bool | None = None


class GuardrailPolicyUpdate(BaseModel):
    tools: list[str] = Field(default_factory=list)
