import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.models import Sensitivity
from app.tools.registry import ToolDefinition, ToolRegistry, tool_registry


class ClassifyTicketInput(BaseModel):
    text: str = Field(min_length=1)
    source: str | None = None


class ClassifyTicketOutput(BaseModel):
    intent: str
    confidence: float = Field(ge=0, le=1)
    labels: list[str] = Field(default_factory=list)
    rationale: str


class DetectPriorityInput(BaseModel):
    text: str = Field(min_length=1)
    customer_tier: str | None = None
    intent: str | None = None


class DetectPriorityOutput(BaseModel):
    priority: Literal["low", "normal", "high", "urgent"]
    score: int = Field(ge=0, le=100)
    rationale: str


class ExtractEntitiesInput(BaseModel):
    text: str = Field(min_length=1)


class ExtractEntitiesOutput(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    order_ids: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    issue_type: str | None = None
    dates: list[str] = Field(default_factory=list)
    raw_entities: dict[str, list[str]] = Field(default_factory=dict)


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)
    document_types: list[str] = Field(default_factory=list)


class KnowledgeBaseResult(BaseModel):
    title: str
    source: str
    snippet: str
    score: float = Field(ge=0, le=1)
    tags: list[str] = Field(default_factory=list)


class SearchKnowledgeBaseOutput(BaseModel):
    query: str
    results: list[KnowledgeBaseResult]


class DraftEmailResponseInput(BaseModel):
    intent: str
    customer_name: str | None = None
    priority: str | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    policy_context: list[str] = Field(default_factory=list)
    tone: Literal["professional", "friendly", "concise"] = "professional"


class DraftEmailResponseOutput(BaseModel):
    subject: str
    body: str
    requires_human_review: bool
    citations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SendEmailInput(BaseModel):
    to: str = Field(min_length=3)
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)

    @field_validator("to")
    @classmethod
    def validate_email_like(cls, value: str) -> str:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("to must be an email-like address")
        return value


class SendEmailOutput(BaseModel):
    provider: str
    provider_message_id: str
    status: Literal["sent"]
    to: str
    subject: str
    sent_at: datetime


class CreateCRMNoteInput(BaseModel):
    note: str = Field(min_length=1)
    customer_id: str | None = None
    customer_email: str | None = None
    ticket_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class CreateCRMNoteOutput(BaseModel):
    crm_note_id: str
    status: Literal["created"]
    summary: str
    tags: list[str] = Field(default_factory=list)


class TicketSummaryInput(BaseModel):
    id: str
    subject: str
    body: str
    priority: str | None = None
    status: str | None = None
    intent: str | None = None


class SummarizeTicketsInput(BaseModel):
    tickets: list[TicketSummaryInput] = Field(min_length=1)
    start_date: str | None = None
    end_date: str | None = None


class SummarizeTicketsOutput(BaseModel):
    ticket_count: int
    top_intents: dict[str, int]
    priority_counts: dict[str, int]
    summary: str
    notable_tickets: list[str] = Field(default_factory=list)


class ReportSectionInput(BaseModel):
    title: str
    content: str


class GenerateReportInput(BaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sections: list[ReportSectionInput] = Field(default_factory=list)
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    audience: str = "support leadership"


class GenerateReportOutput(BaseModel):
    title: str
    markdown: str
    word_count: int
    sections: list[str]
    generated_at: datetime


class ExportReportInput(BaseModel):
    title: str = Field(min_length=1)
    markdown: str = Field(min_length=1)
    format: Literal["pdf", "docx", "html", "md"] = "pdf"
    destination: str | None = None


class ExportReportOutput(BaseModel):
    export_id: str
    status: Literal["exported"]
    format: str
    download_url: str
    expires_at: datetime


MOCK_KNOWLEDGE_BASE = [
    {
        "title": "Refund Policy",
        "source": "mock://kb/refund-policy",
        "tags": ["refund", "orders", "approval"],
        "content": (
            "Refund requests for damaged products require order verification. "
            "Agents may draft responses, but refunds and outbound emails require human approval."
        ),
    },
    {
        "title": "Human Approval Rules",
        "source": "mock://kb/human-approval-rules",
        "tags": ["guardrails", "approval", "sensitive-actions"],
        "content": (
            "Sensitive actions include sending emails, exporting reports, and triggering "
            "refund requests. Internal CRM notes can run automatically but must be audited."
        ),
    },
    {
        "title": "Weekly Support Report Playbook",
        "source": "mock://kb/weekly-support-report",
        "tags": ["reporting", "tickets", "summary"],
        "content": (
            "Weekly support reports include ticket volume, top intents, priority distribution, "
            "notable escalations, and recommended workflow improvements."
        ),
    },
]


def classify_ticket(payload: ClassifyTicketInput) -> ClassifyTicketOutput:
    text = payload.text.lower()
    labels: list[str] = []

    if any(keyword in text for keyword in ["refund", "money back", "return"]):
        intent = "refund_request"
        labels.append("refund")
    elif any(keyword in text for keyword in ["bug", "broken", "error", "not working"]):
        intent = "technical_issue"
        labels.append("technical")
    elif any(keyword in text for keyword in ["invoice", "billing", "charged"]):
        intent = "billing_question"
        labels.append("billing")
    elif any(keyword in text for keyword in ["ship", "delivery", "tracking"]):
        intent = "shipping_question"
        labels.append("shipping")
    else:
        intent = "general_support"
        labels.append("general")

    if any(keyword in text for keyword in ["urgent", "asap", "immediately"]):
        labels.append("urgent_signal")

    confidence = 0.88 if intent != "general_support" else 0.62
    return ClassifyTicketOutput(
        intent=intent,
        confidence=confidence,
        labels=labels,
        rationale=f"Matched deterministic keyword rules for {intent}.",
    )


def detect_priority(payload: DetectPriorityInput) -> DetectPriorityOutput:
    text = payload.text.lower()
    score = 35
    reasons: list[str] = []

    if payload.intent == "refund_request" or "refund" in text:
        score += 20
        reasons.append("refund request")
    if any(keyword in text for keyword in ["urgent", "asap", "immediately", "cannot access"]):
        score += 30
        reasons.append("urgent language")
    if any(keyword in text for keyword in ["damaged", "broken", "failed", "error"]):
        score += 15
        reasons.append("service-impacting issue")
    if payload.customer_tier and payload.customer_tier.lower() in {"enterprise", "vip"}:
        score += 15
        reasons.append("high-value customer tier")

    score = min(score, 100)
    if score >= 85:
        priority = "urgent"
    elif score >= 65:
        priority = "high"
    elif score >= 35:
        priority = "normal"
    else:
        priority = "low"

    return DetectPriorityOutput(
        priority=priority,
        score=score,
        rationale=", ".join(reasons) if reasons else "No high-priority signals detected.",
    )


def extract_entities(payload: ExtractEntitiesInput) -> ExtractEntitiesOutput:
    text = payload.text
    product_pattern = (
        r"product\s+([A-Za-z0-9][A-Za-z0-9 -]{0,40}?)"
        r"(?:\s+(?:arrived|is|was|came|failed|broke)|[.,;!?]|$)"
    )
    emails = sorted(
        set(
            match.strip(".,;:!?")
            for match in re.findall(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",
                text,
            )
        )
    )
    order_ids = sorted(
        set(
            match.upper().replace("ORDER ", "").replace("ORDER#", "").replace("#", "")
            for match in re.findall(r"(?:order\s*#?|#)\s*([A-Za-z0-9-]{4,})", text, re.I)
        )
    )
    products = sorted(
        set(
            match.strip(" .,!?:;")
            for match in re.findall(
                product_pattern,
                text,
                re.I,
            )
        )
    )
    dates = sorted(
        set(re.findall(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b", text))
    )
    customer_name = None
    name_match = re.search(
        r"(?:my name is|i am|i'm)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)",
        text,
        re.I,
    )
    if name_match:
        customer_name = name_match.group(1)

    lowered = text.lower()
    if "refund" in lowered:
        issue_type = "refund"
    elif any(keyword in lowered for keyword in ["damaged", "broken"]):
        issue_type = "damaged_product"
    elif "billing" in lowered or "charged" in lowered:
        issue_type = "billing"
    else:
        issue_type = None

    return ExtractEntitiesOutput(
        customer_name=customer_name,
        customer_email=emails[0] if emails else None,
        order_ids=order_ids,
        products=products,
        issue_type=issue_type,
        dates=dates,
        raw_entities={"emails": emails, "order_ids": order_ids, "products": products},
    )


def search_knowledge_base(payload: SearchKnowledgeBaseInput) -> SearchKnowledgeBaseOutput:
    query_terms = tokenize(payload.query)
    results: list[KnowledgeBaseResult] = []

    for document in MOCK_KNOWLEDGE_BASE:
        document_terms = tokenize(
            " ".join([document["title"], document["content"], *document["tags"]])
        )
        if not query_terms:
            score = 0.0
        else:
            score = len(query_terms & document_terms) / len(query_terms)

        if score > 0:
            results.append(
                KnowledgeBaseResult(
                    title=document["title"],
                    source=document["source"],
                    snippet=document["content"][:220],
                    score=round(min(score, 1.0), 3),
                    tags=list(document["tags"]),
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)
    return SearchKnowledgeBaseOutput(query=payload.query, results=results[: payload.limit])


def draft_email_response(payload: DraftEmailResponseInput) -> DraftEmailResponseOutput:
    customer_name = payload.customer_name or "there"
    order_ids = payload.entities.get("order_ids") or payload.entities.get("order_id") or []
    if isinstance(order_ids, str):
        order_ids = [order_ids]

    order_text = f" for order #{order_ids[0]}" if order_ids else ""
    subject = build_subject(payload.intent, order_text)
    review_warnings = [
        "Outbound customer email requires human approval before sending.",
    ]
    if payload.intent == "refund_request":
        review_warnings.append("Do not promise an actual refund until the reviewer approves.")

    context_sentence = ""
    if payload.policy_context:
        context_sentence = f"\n\nRelevant policy note: {payload.policy_context[0]}"

    body = (
        f"Hi {customer_name},\n\n"
        f"Thanks for reaching out{order_text}. I reviewed the details and prepared the next "
        "step for a support specialist to verify before any sensitive action is taken."
        f"{context_sentence}\n\n"
        "We will follow up after review.\n\n"
        "Best,\nSupport Team"
    )

    return DraftEmailResponseOutput(
        subject=subject,
        body=body,
        requires_human_review=True,
        citations=[item for item in payload.policy_context[:3]],
        warnings=review_warnings,
    )


def send_email(payload: SendEmailInput) -> SendEmailOutput:
    return SendEmailOutput(
        provider="mock_email",
        provider_message_id=f"mock_email_{uuid.uuid4().hex[:12]}",
        status="sent",
        to=payload.to,
        subject=payload.subject,
        sent_at=datetime.now(UTC),
    )


def create_crm_note(payload: CreateCRMNoteInput) -> CreateCRMNoteOutput:
    summary = payload.note.strip().splitlines()[0][:160]
    return CreateCRMNoteOutput(
        crm_note_id=f"mock_crm_note_{uuid.uuid4().hex[:12]}",
        status="created",
        summary=summary,
        tags=payload.tags,
    )


def summarize_tickets(payload: SummarizeTicketsInput) -> SummarizeTicketsOutput:
    intent_counts = Counter(ticket.intent or "unknown" for ticket in payload.tickets)
    priority_counts = Counter(ticket.priority or "unknown" for ticket in payload.tickets)
    notable_tickets = [
        ticket.id
        for ticket in payload.tickets
        if (ticket.priority or "").lower() in {"high", "urgent"}
    ][:5]
    top_intent = intent_counts.most_common(1)[0][0]

    summary = (
        f"Reviewed {len(payload.tickets)} tickets. Top intent is {top_intent}. "
        f"High-signal tickets: {len(notable_tickets)}."
    )

    return SummarizeTicketsOutput(
        ticket_count=len(payload.tickets),
        top_intents=dict(intent_counts),
        priority_counts=dict(priority_counts),
        summary=summary,
        notable_tickets=notable_tickets,
    )


def generate_report(payload: GenerateReportInput) -> GenerateReportOutput:
    lines = [f"# {payload.title}", "", payload.summary, ""]
    if payload.metrics:
        lines.extend(["## Metrics", ""])
        for key, value in payload.metrics.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    section_titles: list[str] = []
    for section in payload.sections:
        section_titles.append(section.title)
        lines.extend([f"## {section.title}", "", section.content, ""])

    markdown = "\n".join(lines).strip() + "\n"
    return GenerateReportOutput(
        title=payload.title,
        markdown=markdown,
        word_count=len(markdown.split()),
        sections=section_titles,
        generated_at=datetime.now(UTC),
    )


def export_report(payload: ExportReportInput) -> ExportReportOutput:
    export_id = f"mock_export_{uuid.uuid4().hex[:12]}"
    return ExportReportOutput(
        export_id=export_id,
        status="exported",
        format=payload.format,
        download_url=f"mock://exports/{export_id}.{payload.format}",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )


def register_mock_tools(registry: ToolRegistry | None = None) -> ToolRegistry:
    target = registry or tool_registry
    definitions = [
        ToolDefinition(
            name="classify_ticket",
            description="Classify a support ticket intent using deterministic mock rules.",
            input_model=ClassifyTicketInput,
            output_model=ClassifyTicketOutput,
            handler=classify_ticket,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="detect_priority",
            description="Detect ticket priority using deterministic mock rules.",
            input_model=DetectPriorityInput,
            output_model=DetectPriorityOutput,
            handler=detect_priority,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="extract_entities",
            description="Extract customer, order, product, and issue entities from text.",
            input_model=ExtractEntitiesInput,
            output_model=ExtractEntitiesOutput,
            handler=extract_entities,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="search_knowledge_base",
            description="Search a mock knowledge base by token overlap.",
            input_model=SearchKnowledgeBaseInput,
            output_model=SearchKnowledgeBaseOutput,
            handler=search_knowledge_base,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="draft_email_response",
            description="Draft a customer email response for human review.",
            input_model=DraftEmailResponseInput,
            output_model=DraftEmailResponseOutput,
            handler=draft_email_response,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="send_email",
            description="Mock-send an outbound email after approval.",
            input_model=SendEmailInput,
            output_model=SendEmailOutput,
            handler=send_email,
            sensitivity=Sensitivity.APPROVAL_REQUIRED,
            risk_reason="Outbound email is a sensitive customer-facing action.",
            max_attempts=1,
        ),
        ToolDefinition(
            name="create_crm_note",
            description="Mock-create an internal CRM note and audit the write.",
            input_model=CreateCRMNoteInput,
            output_model=CreateCRMNoteOutput,
            handler=create_crm_note,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="summarize_tickets",
            description="Summarize support tickets for reports.",
            input_model=SummarizeTicketsInput,
            output_model=SummarizeTicketsOutput,
            handler=summarize_tickets,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="generate_report",
            description="Generate a markdown support report from structured sections.",
            input_model=GenerateReportInput,
            output_model=GenerateReportOutput,
            handler=generate_report,
            sensitivity=Sensitivity.SAFE,
            max_attempts=1,
        ),
        ToolDefinition(
            name="export_report",
            description="Mock-export a report after approval.",
            input_model=ExportReportInput,
            output_model=ExportReportOutput,
            handler=export_report,
            sensitivity=Sensitivity.APPROVAL_REQUIRED,
            risk_reason="Exporting reports can disclose operational or customer data.",
            max_attempts=1,
        ),
    ]

    for definition in definitions:
        if target.maybe_get(definition.name) is None:
            target.register(definition)

    return target


def tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 2}


def build_subject(intent: str, order_text: str) -> str:
    if intent == "refund_request":
        return f"Refund request update{order_text}"
    if intent == "technical_issue":
        return "Support update on your technical issue"
    if intent == "billing_question":
        return "Billing support update"
    return "Support request update"
