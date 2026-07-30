from app.models import Sensitivity

SAFE_TOOL_NAMES = frozenset(
    {
        "classify_ticket",
        "detect_priority",
        "extract_entities",
        "search_knowledge_base",
        "draft_email_response",
        "create_crm_note",
        "summarize_tickets",
        "generate_report",
    }
)

APPROVAL_REQUIRED_TOOL_NAMES = frozenset(
    {
        "send_email",
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


SAFE_TOOLS = SAFE_TOOL_NAMES
APPROVAL_REQUIRED_TOOLS = APPROVAL_REQUIRED_TOOL_NAMES
BLOCKED_TOOLS = BLOCKED_TOOL_NAMES

# Mutable runtime overrides, seeded from the default frozensets above.
# `app.api.settings` mutates this dict directly (guardrail/tool settings
# endpoints), so it must be the single source of truth that `catalog_sensitivity`
# reads from -- otherwise policy enforcement silently ignores admin changes.
TOOL_SENSITIVITY_CATALOG: dict[str, str] = {}
for name in SAFE_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = Sensitivity.SAFE.value
for name in APPROVAL_REQUIRED_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = Sensitivity.APPROVAL_REQUIRED.value
for name in BLOCKED_TOOLS:
    TOOL_SENSITIVITY_CATALOG[name] = Sensitivity.BLOCKED.value


def catalog_sensitivity(tool_name: str) -> Sensitivity | None:
    value = TOOL_SENSITIVITY_CATALOG.get(tool_name)
    if value is None:
        return None
    return Sensitivity(value)
