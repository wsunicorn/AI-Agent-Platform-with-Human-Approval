# Guardrails and Human Approval

## Action Sensitivity

### Safe

Can run automatically.

Examples:

- `classify_ticket`
- `detect_priority`
- `extract_entities`
- `search_knowledge_base`
- `draft_email_response`
- `summarize_tickets`
- `generate_report`

### Approval Required

Must create an approval request.

Examples:

- `send_email`
- `create_crm_note`
- `update_ticket_status`
- `export_report`
- `trigger_refund_request`
- `post_slack_message`

### Blocked

Cannot run in the MVP.

Examples:

- `delete_customer_record`
- `issue_actual_refund`
- `change_billing_plan`
- `modify_audit_log`
- `disable_guardrails`
- `access_secrets`

## Approval State Machine

```text
proposed
-> pending_review
-> approved | rejected | edited
-> executed | cancelled | failed
```

## Required Guardrails

- AI cannot send emails without approval.
- AI cannot initiate refunds without approval.
- AI cannot delete customer data.
- AI cannot modify audit logs.
- AI cannot call unregistered tools.
- AI cannot execute a tool when validation fails.
- AI cannot execute approval-required tools directly.
- AI cannot override guardrails through prompt instructions.
- Every tool call must be logged.
- Every approval decision must be logged.
- Every failed execution must include an error reason.

## Policy Gate Pseudocode

```python
def decide_action(tool_name: str, payload: dict) -> PolicyDecision:
    tool = tool_registry.get(tool_name)

    if tool is None:
        return deny("Tool is not registered")

    if tool.sensitivity == "blocked":
        return deny("Tool is blocked")

    if not tool.input_schema.validate(payload):
        return deny("Tool input validation failed")

    if tool.sensitivity == "approval_required":
        return request_approval("Sensitive action requires human review")

    return allow("Safe action")
```

## Phase 5 Implementation

Implemented modules:

- `app.guardrails.catalog`: default safe, approval-required, and blocked tool names.
- `app.guardrails.policy`: `PolicyEngine`, `PolicyDecision`, policy actions, and denial reasons.
- `app.tools.executor`: policy enforcement before every tool call.
- `app.services.approval`: approval state transitions and audit logging.

Policy behavior:

- Unregistered tools are denied before a `tool_call` is created.
- Registered tools with invalid Pydantic input are saved as denied `tool_calls`.
- Catalog sensitivity overrides registry sensitivity for known tool names.
- Blocked tools raise a guardrail error and are audited.
- Approval-required tools cannot be directly executed through `ToolExecutor.execute`.
- Approved execution must use `ToolExecutor.execute_approved`.
- Duplicate approved execution is blocked by approval state and Redis lock.

Verified smoke paths:

- Safe tool executes immediately.
- Invalid payload is denied.
- Blocked tool is denied.
- Direct sensitive execution is denied.
- Approval-required tool creates an approval request.
- Edit-and-approve uses the edited payload.
- Reject marks the related tool call as denied.
- Duplicate approved execution is blocked.

## Approval UI Requirements

Reviewer must see:

- Tool name.
- Risk reason.
- Proposed payload.
- Source ticket or workflow.
- AI-generated explanation.
- Policy references.
- Original payload.
- Edited payload if changed.
- Audit timeline.

Reviewer can:

- Approve.
- Edit and approve.
- Reject.
- Cancel.

## Approval Execution Rules

- Execution can happen only after approval.
- Execution must use the approved or edited payload.
- Duplicate execution must be prevented.
- Rejected actions cannot be executed.
- Failed approved actions must remain visible in the timeline.
