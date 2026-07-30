# Agent Workflows

Two LangGraph graphs exist, built by `app/agents/support_graph.py` and
`app/agents/workflow_graph.py`, with node implementations in
`app/agents/nodes.py`. Both are compiled fresh per run
(`graph.compile()`, no checkpointer) and invoked once via `ainvoke` from a
FastAPI `BackgroundTasks` coroutine in `app/api/agent_runs.py`.

## State

`app/agents/state.py` defines two `TypedDict`s. Key fields actually read/written:

**`SupportAgentState`**: `run_id`, `mode`, `input_text`, `ticket_subject`,
`ticket_customer_email`, `ticket_customer_name`, `ticket_priority`,
`ticket_status`, `intent`, `intent_confidence`, `priority`, `entities`,
`retrieval_query`, `retrieved_context`, `citations`, `draft_response`,
`planned_actions`, `safe_actions`, `approval_required_actions`,
`blocked_actions`, `approval_requests`, `approved_actions` (declared but never
populated — see below), `tool_results`, `final_output`, `errors`,
`current_step`, `steps_completed`.

**`WorkflowAutomationState`**: `run_id`, `mode`, `input_text`, `instruction`,
`plan`, `plan_validated` (declared but never set), `retrieved_context`/`citations`
(declared but never populated — workflow automation mode never calls
retrieval), `safe_actions`, `approval_required_actions`, `blocked_actions`,
`approval_requests`, `approved_actions` (unused, same as above), `tool_results`,
`final_report`, `errors`, `current_step`, `steps_completed`.

## Support Agent Workflow (`build_support_graph`)

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
-> [conditional] approval_required_actions present?
     yes -> create_approval_requests -> END   (run pauses here; see below)
     no  -> finalize_output -> END
```

### Node behavior

- **`normalize_input`**: trims `input_text`.
- **`classify_intent`**: asks the LLM router (`TaskPurpose.CLASSIFICATION`) for
  one of `refund_request, product_issue, billing_inquiry, account_issue,
  general_inquiry, escalation, feedback, data_request` + confidence. On any
  LLM/JSON failure, falls back to the deterministic `classify_ticket` mock-tool
  keyword rules, remapped to the LLM's label set.
- **`detect_priority`**: LLM call for `low/normal/high/urgent`, falling back to
  the deterministic `detect_priority` mock tool on failure.
- **`extract_entities`**: LLM call for customer name/email/order id/product/
  issue type/dates/amounts; on failure, returns an empty dict (no deterministic
  fallback here, unlike classification/priority).
- **`retrieve_policy_context`**: builds a query as `f"{intent}: {text}"`, runs
  `hybrid_search(limit=20)`, reranks to `top_k=5`, packs context with
  citations. On failure, continues with empty context/citations rather than
  failing the run.
- **`draft_response`**: LLM call instructed not to promise refunds or
  irreversible actions directly; on failure, `draft_response` is left empty
  and the error is recorded in `state["errors"]`, but the run continues.
- **`plan_tool_actions`**: asks the LLM to propose actions restricted to
  `SUPPORT_ACTION_TOOLS = {send_email, create_crm_note, export_report}` (a
  hardcoded allow-list in `nodes.py`, independent of the guardrail catalog).
  `_normalize_planned_actions` then post-processes the LLM's output: it drops
  any proposed action whose `tool_name` isn't in that set, synthesizes a
  `send_email` action from the draft response if the LLM didn't propose one
  and a valid customer email can be found, and adjusts the `create_crm_note`
  text so it doesn't claim an email was "sent" while that email is still
  pending approval.
- **`policy_gate`**: runs every planned action through `PolicyEngine.decide`
  and buckets it into `safe_actions` / `approval_required_actions` /
  `blocked_actions`. In the support flow, actions have already been filtered
  to the 3-tool allow-list above, so `blocked_actions` is effectively always
  empty here in practice — the policy gate's blocked branch is really only
  reachable through the API layer directly, not through this graph (see
  [`GUARDRAILS_AND_APPROVALS.md`](GUARDRAILS_AND_APPROVALS.md)).
- **`execute_safe_tools`**: runs `ToolExecutor.execute` for each safe action
  (e.g. `create_crm_note`), committing after each batch.
- **`create_approval_requests`**: for each approval-required action, calls
  `ToolExecutor.execute` with `require_approval=True`, which creates the
  `tool_calls` + `approval_requests` rows and returns immediately (no
  execution). The node records the created approval ids in
  `state["approval_requests"]`.
- **`finalize_output`**: only reached when there were no approval-required
  actions. Builds a summary string and a `final_output` dict from whatever
  ran in this single pass.

### The "pause" is the graph ending, not a resumable checkpoint

There is no `wait_for_human_decision` node. When `create_approval_requests`
runs, the graph's next edge is `END` — the `ainvoke` call simply returns.
`app/api/agent_runs.py` then sets the run's status to `WAITING_FOR_APPROVAL`.
Later, when a reviewer approves and calls `POST /approvals/{id}/execute`, that
request handler calls `ToolExecutor.execute_approved` directly — a plain
service call against the database, with no relationship to the LangGraph
run at all. The graph is never resumed, checkpointed, or re-entered.

Both graphs *do* define an `execute_approved_tools` node (and
`support_graph.py` defines a `_has_approved_actions` conditional-edge
function for it), but neither graph ever wires an edge into that node, and
nothing ever populates `state["approved_actions"]`. It is dead code today —
present for a "resume the graph after approval" design that was never
finished. If you want that behavior for real, you'd need a LangGraph
checkpointer (e.g. Postgres-backed) plus code that resumes the compiled graph
by run id when an approval executes, instead of calling `ToolExecutor`
directly from the API layer.

## Workflow Automation Mode (`build_workflow_graph`)

```text
parse_instruction
-> generate_plan
-> policy_gate
-> execute_safe_tools
-> [conditional] approval_required_actions present?
     yes -> create_approval_requests -> END
     no  -> generate_final_report -> END
```

This is simpler than the support workflow and simpler than the original
design draft implied:

- There is **no retrieval step** in this mode (`retrieved_context`/`citations`
  in `WorkflowAutomationState` are declared but never populated) — instructions
  are planned purely from the LLM's own knowledge plus whatever
  `generate_plan`'s prompt includes.
- There is **no `validate_plan_tools` node** — `generate_plan` asks the LLM to
  choose from a hardcoded tool list (`summarize_tickets`, `generate_report`,
  `export_report`, `search_knowledge_base`) but nothing rejects a plan step
  that names a tool outside that list before `policy_gate` runs; an
  out-of-list tool name would simply be denied later as "unregistered".
- **`generate_final_report`** always runs the LLM to summarize `tool_results`
  against the original instruction, even when there were zero tool results.

## Workflow Rules (what actually holds)

- No node calls a tool directly — every side effect goes through
  `ToolExecutor.execute`, which re-applies the policy gate regardless of what
  `plan_tool_actions`/`generate_plan` already decided.
- Every tool call and approval transition writes an audit log row
  (`AuditService.record`), which is also how realtime events reach the
  frontend — there's no separate "workflow event" concept.
- A node that catches an LLM/tool failure records it into `state["errors"]`
  and continues rather than aborting the run; only truly unexpected exceptions
  (uncaught by a node) mark the whole `agent_runs` row `FAILED`
  (`app/api/agent_runs.py`'s `except Exception` around `ainvoke`).
- Sensitive actions always stop the run at `create_approval_requests -> END`;
  there is no code path where the same `ainvoke` call also executes an
  approved action.
