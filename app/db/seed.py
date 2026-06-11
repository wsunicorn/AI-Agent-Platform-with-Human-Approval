import asyncio
import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_sessionmaker
from app.models import (
    ActorType,
    AgentMode,
    AgentRun,
    AgentRunStatus,
    ApprovalRequest,
    ApprovalStatus,
    AuditLog,
    InputType,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentType,
    ModelConfig,
    ModelMode,
    ModelProvider,
    ModelPurpose,
    Priority,
    Sensitivity,
    Ticket,
    TicketStatus,
    ToolCall,
    ToolCallStatus,
)


def checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def demo_embedding(seed: int, dimensions: int = 768) -> list[float]:
    return [(((index + seed) % 17) + 1) / 17 for index in range(dimensions)]


async def upsert_model_config(
    session: AsyncSession,
    *,
    provider: ModelProvider,
    model_name: str,
    mode: ModelMode,
    purpose: ModelPurpose,
    endpoint_url: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    is_default: bool = False,
) -> None:
    config = await session.scalar(
        select(ModelConfig).where(
            ModelConfig.provider == provider,
            ModelConfig.model_name == model_name,
            ModelConfig.purpose == purpose,
        )
    )

    if config is None:
        session.add(
            ModelConfig(
                provider=provider,
                model_name=model_name,
                endpoint_url=endpoint_url,
                mode=mode,
                purpose=purpose,
                temperature=temperature,
                max_tokens=max_tokens,
                is_default=is_default,
            )
        )
        return

    config.endpoint_url = endpoint_url
    config.mode = mode
    config.temperature = temperature
    config.max_tokens = max_tokens
    config.is_default = is_default


async def seed_model_configs(session: AsyncSession) -> None:
    await upsert_model_config(
        session,
        provider=ModelProvider.GEMINI,
        model_name="gemini-3.1-flash-lite",
        mode=ModelMode.HOSTED,
        purpose=ModelPurpose.DEFAULT,
        temperature=0.2,
        max_tokens=4096,
        is_default=True,
    )
    await upsert_model_config(
        session,
        provider=ModelProvider.OLLAMA,
        model_name="gemma3:4b",
        endpoint_url="http://localhost:11434",
        mode=ModelMode.LOCAL,
        purpose=ModelPurpose.FALLBACK,
        temperature=0.2,
        max_tokens=2048,
        is_default=True,
    )
    await upsert_model_config(
        session,
        provider=ModelProvider.OLLAMA,
        model_name="qwen3:8b",
        endpoint_url="http://localhost:11434",
        mode=ModelMode.LOCAL,
        purpose=ModelPurpose.QUALITY,
        temperature=0.2,
        max_tokens=4096,
    )
    await upsert_model_config(
        session,
        provider=ModelProvider.OLLAMA,
        model_name="qwen2.5:3b",
        endpoint_url="http://localhost:11434",
        mode=ModelMode.LOCAL,
        purpose=ModelPurpose.ROUTING,
        temperature=0.1,
        max_tokens=1024,
    )
    await upsert_model_config(
        session,
        provider=ModelProvider.LOCAL,
        model_name="nomic-embed-text-v2-moe",
        endpoint_url="http://localhost:11434",
        mode=ModelMode.LOCAL,
        purpose=ModelPurpose.EMBEDDING,
        temperature=0.0,
        max_tokens=1024,
        is_default=True,
    )


async def seed_ticket(session: AsyncSession) -> Ticket:
    ticket = await session.scalar(
        select(Ticket).where(Ticket.subject == "Refund request for order #12345")
    )
    if ticket is not None:
        return ticket

    ticket = Ticket(
        source="email",
        customer_name="Maya Chen",
        customer_email="maya.chen@example.com",
        subject="Refund request for order #12345",
        body=(
            "I want a refund for order #12345. The product arrived damaged and I need help "
            "as soon as possible."
        ),
        status=TicketStatus.TRIAGED,
        priority=Priority.HIGH,
        intent="refund_request",
        issue_type="damaged_product",
        extracted_entities={
            "order_id": "12345",
            "product_condition": "damaged",
            "customer_name": "Maya Chen",
        },
    )
    session.add(ticket)
    await session.flush()
    return ticket


async def seed_knowledge(session: AsyncSession) -> None:
    documents = [
        {
            "title": "Refund Policy",
            "source": "seed://policies/refund",
            "tags": ["refund", "orders", "support"],
            "document_type": KnowledgeDocumentType.POLICY,
            "content": (
                "Refunds for damaged products can be approved after order verification. "
                "Support agents may draft the response, but payment refunds and outbound "
                "customer emails require human approval before execution."
            ),
            "chunks": [
                (
                    "Refunds for damaged products can be approved after order verification. "
                    "Agents must extract the order ID and cite the applicable refund policy."
                ),
                (
                    "Payment refunds and outbound customer emails are sensitive actions. "
                    "They require explicit human approval before execution."
                ),
            ],
        },
        {
            "title": "Weekly Support Report Playbook",
            "source": "seed://playbooks/weekly-support-report",
            "tags": ["reporting", "support", "manager"],
            "document_type": KnowledgeDocumentType.PLAYBOOK,
            "content": (
                "Weekly support reports should include ticket volume, top intents, priority "
                "distribution, notable escalations, and suggested workflow improvements."
            ),
            "chunks": [
                (
                    "A weekly support report includes ticket volume, top intents, priority "
                    "distribution, escalations, and follow-up actions."
                ),
                (
                    "Exporting a final report is approval-required when it contains customer "
                    "data or operational metrics."
                ),
            ],
        },
    ]

    for document_data in documents:
        content_checksum = checksum(document_data["content"])
        document = await session.scalar(
            select(KnowledgeDocument).where(KnowledgeDocument.checksum == content_checksum)
        )

        if document is None:
            document = KnowledgeDocument(
                title=document_data["title"],
                content=document_data["content"],
                source=document_data["source"],
                tags=document_data["tags"],
                document_type=document_data["document_type"],
                version=1,
                checksum=content_checksum,
            )
            session.add(document)
            await session.flush()

        for index, chunk_content in enumerate(document_data["chunks"]):
            chunk = await session.scalar(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.knowledge_document_id == document.id,
                    KnowledgeChunk.chunk_index == index,
                )
            )
            if chunk is None:
                session.add(
                    KnowledgeChunk(
                        knowledge_document_id=document.id,
                        chunk_index=index,
                        content=chunk_content,
                        embedding=demo_embedding(index + len(document.title)),
                        embedding_model="nomic-embed-text-v2-moe",
                        token_count=len(chunk_content.split()),
                        chunk_metadata={"seeded": True, "title": document.title},
                    )
                )


async def seed_demo_run(session: AsyncSession, ticket: Ticket) -> None:
    existing_run = await session.scalar(
        select(AgentRun).where(
            AgentRun.ticket_id == ticket.id,
            AgentRun.created_by == "seed",
        )
    )
    if existing_run is not None:
        return

    now = datetime.now(UTC)
    agent_run = AgentRun(
        ticket_id=ticket.id,
        mode=AgentMode.SUPPORT_AGENT,
        input_type=InputType.TICKET,
        input_text=ticket.body,
        status=AgentRunStatus.WAITING_FOR_APPROVAL,
        final_output={
            "draft_response": (
                "Hi Maya, thanks for reaching out. I found order #12345 and can help with "
                "the damaged product refund request. A support specialist will review this "
                "before anything is sent or processed."
            )
        },
        created_by="seed",
        started_at=now,
    )
    session.add(agent_run)
    await session.flush()

    draft_tool_call = ToolCall(
        agent_run_id=agent_run.id,
        tool_name="draft_email_response",
        sensitivity=Sensitivity.SAFE,
        input_payload={"ticket_id": str(ticket.id), "intent": "refund_request"},
        output_payload={"draft": agent_run.final_output["draft_response"]},
        status=ToolCallStatus.COMPLETED,
        retry_count=0,
        started_at=now,
        completed_at=now,
    )
    session.add(draft_tool_call)

    send_email_call = ToolCall(
        agent_run_id=agent_run.id,
        tool_name="send_email",
        sensitivity=Sensitivity.APPROVAL_REQUIRED,
        input_payload={
            "to": ticket.customer_email,
            "subject": "Refund request for order #12345",
            "body": agent_run.final_output["draft_response"],
        },
        status=ToolCallStatus.WAITING_FOR_APPROVAL,
        retry_count=0,
        timeout_ms=10000,
    )
    session.add(send_email_call)
    await session.flush()

    approval_request = ApprovalRequest(
        agent_run_id=agent_run.id,
        tool_call_id=send_email_call.id,
        tool_name=send_email_call.tool_name,
        proposed_payload=send_email_call.input_payload,
        risk_reason="Outbound email is a sensitive action and requires human approval.",
        status=ApprovalStatus.PENDING_REVIEW,
    )
    session.add(approval_request)
    await session.flush()

    session.add_all(
        [
            AuditLog(
                actor_type=ActorType.SYSTEM,
                actor_id="seed",
                event_type="ticket.seeded",
                entity_type="ticket",
                entity_id=str(ticket.id),
                before_state=None,
                after_state={"status": ticket.status, "priority": ticket.priority},
                event_metadata={"source": "phase_3_seed"},
            ),
            AuditLog(
                actor_type=ActorType.AGENT,
                actor_id="seed_support_agent",
                event_type="approval.requested",
                entity_type="approval_request",
                entity_id=str(approval_request.id),
                before_state=None,
                after_state={
                    "status": approval_request.status,
                    "tool_name": approval_request.tool_name,
                },
                event_metadata={"agent_run_id": str(agent_run.id)},
            ),
        ]
    )


async def seed() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await seed_model_configs(session)
        ticket = await seed_ticket(session)
        await seed_knowledge(session)
        await seed_demo_run(session, ticket)
        await session.commit()

    print("Seed data is ready.")


if __name__ == "__main__":
    asyncio.run(seed())
