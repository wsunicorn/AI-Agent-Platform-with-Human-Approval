# Guardrails and Human Approval

## How a tool call is actually classified

`app/guardrails/policy.py:PolicyEngine.decide` is the single gate every tool
call passes through (`ToolExecutor.execute`/`execute_approved` call it, and
LangGraph's `policy_gate` node calls it a second time before that). The order
matters:

1. **Is the tool registered?** (`ToolRegistry.maybe_get`, populated at startup
   by `register_mock_tools`). If not, **deny as `unregistered_tool`** —
   before anything else is checked, and before a `tool_calls` row is even
   created.
2. **What does the catalog say?** `catalog_sensitivity(tool_name)` looks the
   name up in `TOOL_SENSITIVITY_CATALOG` (`app/guardrails/catalog.py`), a
   mutable dict seeded from the three name sets below. If the tool isn't in
   the catalog, the tool definition's own declared sensitivity is used
   instead.
3. `blocked` → deny. Invalid Pydantic input → deny. `approval_required` →
   create an approval request. Otherwise → allow.

**Consequence:** a tool name only reaches the "blocked" or "approval_required"
branch if it is *also* registered with a real `ToolDefinition` (input/output
models + handler). Today, only 10 tools are registered
(`app/tools/mock_tools.py:register_mock_tools`), and only 2 of them are
`approval_required`. Every other name below that appears in the catalog but
has no registered implementation would be denied as *unregistered*, not
routed through the blocked/approval branch — worth knowing if you're using
this catalog as a specification for guardrail behavior rather than as a
description of two tools.

### Safe (execute immediately, still fully audited)

Registered and implemented:

- `classify_ticket`, `detect_priority`, `extract_entities`,
  `search_knowledge_base`, `draft_email_response`, `create_crm_note`,
  `summarize_tickets`, `generate_report`

`create_crm_note` looks like it should be sensitive (it writes an internal
record), but it's intentionally `safe`: it still creates a `tool_calls` row
and an audit log entry (`tool_call.started` / `tool_call.completed`), it's
just not gated behind a human approval step. "Safe" in this system means
"auto-executes", not "unaudited".

### Approval required (creates an `approval_requests` row, execution paused)

Registered and implemented:

- `send_email` — outbound customer email.
- `export_report` — report export/disclosure.

Catalog names with **no registered tool** (would be denied as unregistered
today, not routed to an approval queue, if anything tried to call them):

- `update_ticket_status`, `trigger_refund_request`, `post_slack_message`

### Blocked (cannot run)

Catalog names, **none of which are registered tools either** — same caveat as
above applies:

- `delete_customer_record`, `issue_actual_refund`, `change_billing_plan`,
  `modify_audit_log`, `disable_guardrails`, `access_secrets`

If you want a real demo of the "blocked" branch specifically firing (as
opposed to "unregistered tool" firing), you have to register a `ToolDefinition`
for one of these names first — `tests/test_tool_executor.py`'s blocked-tool
test does this by injecting a definition directly into a `ToolRegistry`
rather than exercising the full agent workflow.

## Approval State Machine

Enum: `app/models/enums.py:ApprovalStatus` — `proposed`, `pending_review`,
`approved`, `rejected`, `edited`, `executed`, `cancelled`, `failed`.

Real transitions, from `app/services/approval.py`:

```text
pending_review --approve()-------------------> approved
pending_review --approve(edited_payload)-----> edited
pending_review --reject()--------------------> rejected
approved       --reject()--------------------> rejected   (yes — approved can still be rejected before execution)
edited         --reject()--------------------> rejected
approved/edited --execute success------------> executed
approved/edited --execute failure------------> failed
```

`cancelled` is defined in the enum but **no code path sets it.** The "Cancel"
button in the frontend's payload editor (`ApprovalDetail.tsx`) only cancels
an in-progress *edit* (discards unsaved JSON changes); it does not cancel the
underlying approval request.

Every transition:

- Runs under `SELECT ... FOR UPDATE` on the `approval_requests` row
  (`ApprovalService.get_for_update`), so concurrent approve/reject/execute
  calls on the same approval serialize correctly.
- Writes an audit log row (`approval.created`, `approval.approved`,
  `approval.edited`, `approval.rejected`, `approval.executed`,
  `approval.failed`).
- `reject()` also flips the linked `tool_calls.status` to `denied`.
- `execute` additionally takes a Redis lock keyed on the approval id
  (`approval-execution:{approval_id}`, TTL from
  `approval_execution_lock_ttl_seconds`) before re-checking status under the
  row lock — belt-and-suspenders against a double-click or a retried request
  executing the same approval twice.

## Required Guardrails (what's actually enforced today)

- The agent cannot send emails or export reports without approval — enforced
  by `PolicyEngine`/`ToolExecutor`, not by prompting.
- The agent cannot execute an approval-required tool directly:
  `ToolExecutor.execute(..., require_approval=False)` on such a tool raises
  `ToolApprovalRequiredError` and records a `guardrail.denied` audit event.
- The agent cannot call an unregistered tool — denied before any `tool_calls`
  row exists.
- The agent cannot execute a tool whose payload fails Pydantic validation —
  denied and audited.
- Every tool call and every approval decision is logged to `audit_logs`.
- Every failed execution stores `error_message` on the `tool_calls` row and is
  audited as `tool_call.failed`.
- Guardrail configuration (`/settings/tools`, `/settings/guardrail-policies`)
  is a live, mutable, **process-global** override: changing a tool's
  sensitivity through the Settings screen changes what `PolicyEngine` actually
  enforces for every subsequent call, immediately, for as long as the process
  stays up (it is not persisted anywhere, so a restart reverts to the
  hardcoded defaults in `catalog.py`).

There's no code-level defense against "prompt injection to override
guardrails" beyond the structural fact that the LLM's output only ever
becomes a *proposed* tool call — `PolicyEngine.decide` runs on every call
regardless of what the model said, so there's no prompt text that can skip it.

## Approval UI (what `ApprovalDetail.tsx` / `ApprovalQueue.tsx` actually show)

- Tool name, risk reason, proposed payload, edited payload (if any), a
  side-by-side JSON diff when edited, status badge, reviewer, reviewer
  comment, reviewed/executed timestamps.
- Reviewer actions: **Approve, Edit-and-approve, Reject, Execute** (once
  approved/edited). There is no Cancel-the-approval action (see above).
- Reviewer identity is not real auth — every action is attributed to the
  hardcoded string `"admin"` from the frontend, not a signed-in user.
