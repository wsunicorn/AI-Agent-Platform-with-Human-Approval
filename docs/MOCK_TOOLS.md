# Mock Tools

Phase 6 implements deterministic tool handlers that can be executed through the
same registry, guardrail, approval, audit, retry, and validation path as real
integrations.

The goal is to make the MVP demoable before connecting Zendesk, Gmail, Slack,
CRM, or report export providers.

## Tool Inventory

| Tool | Sensitivity | Purpose |
| --- | --- | --- |
| `classify_ticket` | Safe | Classify support intent from ticket text. |
| `detect_priority` | Safe | Detect priority from text, intent, and customer tier. |
| `extract_entities` | Safe | Extract customer name, email, order IDs, products, issue type, and dates. |
| `search_knowledge_base` | Safe | Search the mock policy and playbook knowledge base. |
| `draft_email_response` | Safe | Draft a customer response for review. |
| `create_crm_note` | Safe | Mock-create an audited internal CRM note. |
| `summarize_tickets` | Safe | Summarize ticket volume, intent mix, priority mix, and notable tickets. |
| `generate_report` | Safe | Generate a markdown support report from structured inputs. |
| `send_email` | Approval required | Mock-send an outbound email after human approval. |
| `export_report` | Approval required | Mock-export a generated report after human approval. |

## Implementation

Core file:

- `app/tools/mock_tools.py`

Startup registration:

- `app/main.py` registers mock tools for the FastAPI process.
- `app/workers/worker.py` registers mock tools for the worker process.

Tests:

- `tests/test_mock_tools.py`

All tool inputs and outputs are Pydantic models. The `ToolExecutor` validates
input before execution and validates output before writing the completed
`tool_calls.output_payload`.

## Guardrail Behavior

Safe tools execute immediately:

- `classify_ticket`
- `detect_priority`
- `extract_entities`
- `search_knowledge_base`
- `draft_email_response`
- `create_crm_note`
- `summarize_tickets`
- `generate_report`

Customer-facing or disclosure-sensitive mock integrations pause for review:

- `send_email`
- `export_report`

Direct execution of sensitive tools with `require_approval=False` is blocked by
the Phase 5 policy engine.

These 10 tools are the *only* ones with a real handler registered. The
guardrail catalog (`app/guardrails/catalog.py`) also names several
`approval_required`/`blocked` tools that have no registered implementation —
see [`GUARDRAILS_AND_APPROVALS.md`](GUARDRAILS_AND_APPROVALS.md) for what
actually happens if one of those names is called.

## Demo Flow

Refund ticket example:

```text
Input ticket
-> classify_ticket
-> detect_priority
-> extract_entities
-> search_knowledge_base
-> draft_email_response
-> create_crm_note executes and is audited
-> send_email waits for approval
-> reviewer approves
-> send_email executes
```

Weekly report example:

```text
Manager instruction
-> summarize_tickets
-> generate_report
-> export_report waits for approval
-> reviewer approves
-> export_report executes
```

## Verification

Phase 6 was verified with:

```powershell
python -m ruff check app tests
python -m pytest tests
python -m compileall app tests alembic
```

Additional smoke coverage executed all 10 mock tools through `ToolExecutor` in
one database transaction:

- 7 safe tools completed automatically.
- 3 sensitive tools created approval requests.
- 3 approved sensitive tools executed successfully.
- 10 tool calls were created in the transaction.
- The transaction was rolled back after verification.
