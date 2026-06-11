from app.tools.mock_tools import (
    ClassifyTicketInput,
    CreateCRMNoteInput,
    DetectPriorityInput,
    DraftEmailResponseInput,
    ExportReportInput,
    ExtractEntitiesInput,
    GenerateReportInput,
    ReportSectionInput,
    SearchKnowledgeBaseInput,
    SendEmailInput,
    SummarizeTicketsInput,
    TicketSummaryInput,
    classify_ticket,
    create_crm_note,
    detect_priority,
    draft_email_response,
    export_report,
    extract_entities,
    generate_report,
    register_mock_tools,
    search_knowledge_base,
    send_email,
    summarize_tickets,
)
from app.tools.registry import ToolRegistry

EXPECTED_MOCK_TOOLS = {
    "classify_ticket",
    "detect_priority",
    "extract_entities",
    "search_knowledge_base",
    "draft_email_response",
    "send_email",
    "create_crm_note",
    "summarize_tickets",
    "generate_report",
    "export_report",
}


def test_register_mock_tools_is_idempotent() -> None:
    registry = ToolRegistry()

    register_mock_tools(registry)
    register_mock_tools(registry)

    assert {tool.name for tool in registry.list()} == EXPECTED_MOCK_TOOLS


def test_classify_detect_and_extract_refund_ticket() -> None:
    text = (
        "My name is Maya Chen. I want a refund for order #12345. "
        "The product Alpha arrived damaged. Email me at maya@example.com."
    )

    classification = classify_ticket(ClassifyTicketInput(text=text))
    priority = detect_priority(
        DetectPriorityInput(text=text, intent=classification.intent, customer_tier="vip")
    )
    entities = extract_entities(ExtractEntitiesInput(text=text))

    assert classification.intent == "refund_request"
    assert priority.priority in {"high", "urgent"}
    assert entities.customer_name == "Maya Chen"
    assert entities.customer_email == "maya@example.com"
    assert "12345" in entities.order_ids
    assert entities.issue_type == "refund"


def test_search_kb_and_draft_email_response() -> None:
    search_result = search_knowledge_base(
        SearchKnowledgeBaseInput(query="refund approval email", limit=2)
    )
    draft = draft_email_response(
        DraftEmailResponseInput(
            intent="refund_request",
            customer_name="Maya",
            entities={"order_ids": ["12345"]},
            policy_context=[result.snippet for result in search_result.results],
        )
    )

    assert search_result.results
    assert draft.requires_human_review is True
    assert "order #12345" in draft.body
    assert draft.warnings


def test_sensitive_mock_tool_outputs_validate() -> None:
    email = send_email(
        SendEmailInput(to="customer@example.com", subject="Hello", body="Approved body")
    )
    crm_note = create_crm_note(
        CreateCRMNoteInput(note="Customer requested refund review.", tags=["refund"])
    )
    exported = export_report(
        ExportReportInput(title="Weekly Report", markdown="# Weekly Report", format="pdf")
    )

    assert email.status == "sent"
    assert crm_note.status == "created"
    assert exported.status == "exported"
    assert exported.download_url.startswith("mock://exports/")


def test_summarize_tickets_and_generate_report() -> None:
    summary = summarize_tickets(
        SummarizeTicketsInput(
            tickets=[
                TicketSummaryInput(
                    id="T-1",
                    subject="Refund",
                    body="Refund order #12345",
                    priority="high",
                    intent="refund_request",
                ),
                TicketSummaryInput(
                    id="T-2",
                    subject="Billing",
                    body="Invoice question",
                    priority="normal",
                    intent="billing_question",
                ),
            ]
        )
    )
    report = generate_report(
        GenerateReportInput(
            title="Weekly Support Report",
            summary=summary.summary,
            metrics={"ticket_count": summary.ticket_count},
            sections=[
                ReportSectionInput(title="Top Intents", content=str(summary.top_intents)),
                ReportSectionInput(title="Priority Mix", content=str(summary.priority_counts)),
            ],
        )
    )

    assert summary.ticket_count == 2
    assert summary.top_intents["refund_request"] == 1
    assert "Weekly Support Report" in report.markdown
    assert report.word_count > 0
