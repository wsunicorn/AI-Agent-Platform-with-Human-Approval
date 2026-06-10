# Agent Workflows

## LangGraph State

Recommended state fields:

- `run_id`
- `mode`
- `input_text`
- `ticket_id`
- `intent`
- `priority`
- `entities`
- `retrieved_context`
- `draft_response`
- `planned_actions`
- `safe_actions`
- `approval_required_actions`
- `blocked_actions`
- `approval_requests`
- `tool_results`
- `final_output`
- `errors`

## Support Agent Workflow

```text
normalize_input
-> classify_intent
-> detect_priority
-> extract_entities
-> retrieve_policy_context
-> draft_response
-> plan_tool_actions
-> policy_gate
-> execute_safe_tools
-> create_approval_requests
-> wait_for_human_decision
-> execute_approved_tools
-> finalize_output
```

## Workflow Automation Mode

```text
parse_instruction
-> generate_plan
-> validate_plan_tools
-> retrieve_context_if_needed
-> policy_gate
-> execute_safe_tools
-> create_approval_requests
-> wait_for_human_decision
-> execute_approved_tools
-> generate_final_report
```

## Node Responsibilities

### `classify_intent`

- Classify ticket or instruction intent.
- Return a label and confidence score.

### `detect_priority`

- Detect urgency based on text, customer tier, and issue type.
- Return `low`, `medium`, `high`, or `urgent`.

### `extract_entities`

- Extract structured fields such as customer name, email, order ID, product, issue type, and dates.

### `retrieve_policy_context`

- Build retrieval query.
- Run hybrid retrieval.
- Rerank results.
- Pack context with source citations.

### `draft_response`

- Generate a customer-facing draft response.
- Include policy source references.
- Avoid promising refunds or irreversible actions.

### `plan_tool_actions`

- Propose tool actions.
- Mark required payloads.
- Do not execute tools directly.

### `policy_gate`

- Classify every proposed action as safe, approval-required, or blocked.

### `execute_safe_tools`

- Execute safe tools only.
- Validate input and output.
- Write tool call logs.

### `create_approval_requests`

- Persist approval-required actions.
- Publish realtime approval events.

### `wait_for_human_decision`

- Pause workflow until approval state changes.

### `execute_approved_tools`

- Execute final approved payload only.
- Prevent duplicate execution with Redis locks.

## Workflow Rules

- No node may bypass the policy gate.
- Every tool call must write an audit event.
- Every failed node should produce a visible timeline event.
- Sensitive actions must pause the workflow.
- Blocked actions must be denied and logged.

