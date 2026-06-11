from app.models import Sensitivity

SAFE_TOOL_NAMES = frozenset(
    {
        "classify_ticket",
        "detect_priority",
        "extract_entities",
        "search_knowledge_base",
        "draft_email_response",
        "summarize_tickets",
        "generate_report",
    }
)

APPROVAL_REQUIRED_TOOL_NAMES = frozenset(
    {
        "send_email",
        "create_crm_note",
        "update_ticket_status",
        "export_report",
        "trigger_refund_request",
        "post_slack_message",
    }
)

BLOCKED_TOOL_NAMES = frozenset(
    {
        "delete_customer_record",
        "issue_actual_refund",
        "change_billing_plan",
        "modify_audit_log",
        "disable_guardrails",
        "access_secrets",
    }
)


def catalog_sensitivity(tool_name: str) -> Sensitivity | None:
    if tool_name in BLOCKED_TOOL_NAMES:
        return Sensitivity.BLOCKED
    if tool_name in APPROVAL_REQUIRED_TOOL_NAMES:
        return Sensitivity.APPROVAL_REQUIRED
    if tool_name in SAFE_TOOL_NAMES:
        return Sensitivity.SAFE
    return None


SAFE_TOOLS = SAFE_TOOL_NAMES
APPROVAL_REQUIRED_TOOLS = APPROVAL_REQUIRED_TOOL_NAMES
BLOCKED_TOOLS = BLOCKED_TOOL_NAMES

TOOL_SENSITIVITY_CATALOG = {}
for name in SAFE_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = "safe"
for name in APPROVAL_REQUIRED_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = "approval_required"
for name in BLOCKED_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = "blocked"
