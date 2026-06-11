"""LangGraph workflow node implementations."""

from __future__ import annotations

import json
import re
from typing import Any

import structlog

from app.agents.state import SupportAgentState, WorkflowAutomationState
from app.llm import LLMMessage, LLMRequest, get_model_router
from app.llm.router import TaskPurpose

logger = structlog.get_logger(__name__)

SUPPORT_ACTION_TOOLS = {"send_email", "create_crm_note", "export_report"}


def _first_text_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None


def _is_email_like(value: str | None) -> bool:
    if not value or "redacted" in value.lower():
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


def _support_intent(value: str) -> str:
    mapping = {
        "technical_issue": "product_issue",
        "billing_question": "billing_inquiry",
        "shipping_question": "general_inquiry",
        "general_support": "general_inquiry",
    }
    return mapping.get(value, value)


def _customer_email_from_state(state: SupportAgentState) -> str | None:
    direct_email = _first_text_value(state.get("ticket_customer_email"))
    if _is_email_like(direct_email):
        return direct_email

    entities = state.get("entities") or {}
    if not isinstance(entities, dict):
        return None

    for key in ("customer_email", "email", "to"):
        email = _first_text_value(entities.get(key))
        if _is_email_like(email):
            return email

    raw_entities = entities.get("raw_entities")
    if isinstance(raw_entities, dict):
        email = _first_text_value(raw_entities.get("emails"))
        if _is_email_like(email):
            return email

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",
        state.get("input_text", ""),
    )
    email = match.group(0) if match else None
    return email if _is_email_like(email) else None


def _support_email_subject(state: SupportAgentState) -> str:
    intent = state.get("intent") or "general_inquiry"
    entities = state.get("entities") or {}
    order_id = None
    if isinstance(entities, dict):
        order_id = _first_text_value(entities.get("order_id")) or _first_text_value(
            entities.get("order_ids")
        )

    order_text = f" for order #{order_id}" if order_id else ""
    if intent == "refund_request":
        return f"Refund request update{order_text}"
    if intent == "product_issue":
        return f"Support update{order_text}"
    if intent == "billing_inquiry":
        return "Billing support update"
    return "Support request update"


def _normalize_send_email_action(
    action: dict[str, Any],
    state: SupportAgentState,
) -> dict[str, Any] | None:
    payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
    payload = dict(payload)
    if "recipient" in payload and "to" not in payload:
        payload["to"] = payload["recipient"]

    context_email = _customer_email_from_state(state)
    payload_email = _first_text_value(payload.get("to"))
    to = context_email or (payload_email if _is_email_like(payload_email) else None)
    body = (
        _first_text_value(payload.get("body"))
        or _first_text_value(payload.get("draft"))
        or _first_text_value(state.get("draft_response"))
    )
    subject = _first_text_value(payload.get("subject")) or _support_email_subject(state)

    if not to or not body:
        return None

    return {
        **action,
        "tool_name": "send_email",
        "payload": {
            "to": to,
            "subject": subject,
            "body": body,
        },
        "reason": action.get("reason")
        or "Send the reviewed support response to the customer after approval.",
    }


def _normalize_crm_note_action(
    action: dict[str, Any],
    state: SupportAgentState,
    has_email_action: bool,
) -> dict[str, Any]:
    payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
    payload = dict(payload)
    note = _first_text_value(payload.get("note"))
    if not note:
        intent = state.get("intent", "general_inquiry").replace("_", " ")
        note = f"Agent prepared support response for {intent}."

    if has_email_action:
        note = re.sub(r"\b(sent|emailed|delivered)\b", "prepared", note, flags=re.I)
        if "approval" not in note.lower():
            note = f"{note} Outbound customer email is pending human approval."

    payload["note"] = note

    entities = state.get("entities") or {}
    if isinstance(entities, dict):
        payload.setdefault("customer_email", _customer_email_from_state(state))
        order_id = _first_text_value(entities.get("order_id")) or _first_text_value(
            entities.get("order_ids")
        )
        tags = payload.get("tags")
        if not isinstance(tags, list):
            tags = []
        if order_id and "order" not in tags:
            tags.append("order")
        intent = state.get("intent")
        if isinstance(intent, str) and intent not in tags:
            tags.append(intent)
        payload["tags"] = tags

    return {
        **action,
        "tool_name": "create_crm_note",
        "payload": payload,
        "reason": action.get("reason") or "Record an internal, audited support note.",
    }


def _normalize_planned_actions(
    raw_actions: Any,
    state: SupportAgentState,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    has_email_action = False
    candidate_actions: list[dict[str, Any]] = []

    if isinstance(raw_actions, list):
        for item in raw_actions:
            if not isinstance(item, dict):
                continue
            action = {**item, "payload": item.get("payload") or {}}
            if action.get("tool_name") not in SUPPORT_ACTION_TOOLS:
                continue
            if action.get("tool_name") == "send_email":
                email_action = _normalize_send_email_action(action, state)
                if email_action is None:
                    continue
                action = email_action
                has_email_action = True
            candidate_actions.append(action)

    if not has_email_action:
        email_action = _normalize_send_email_action(
            {
                "tool_name": "send_email",
                "payload": {},
                "reason": "Send the drafted customer response after a human approves it.",
            },
            state,
        )
        if email_action is not None:
            candidate_actions.append(email_action)
            has_email_action = True

    for action in candidate_actions:
        if action.get("tool_name") == "create_crm_note":
            normalized.append(_normalize_crm_note_action(action, state, has_email_action))
        else:
            normalized.append(action)

    return normalized


# ── Support Agent Nodes ──────────────────────────────────────────────


async def normalize_input(state: SupportAgentState) -> dict[str, Any]:
    """Clean and normalize the input text."""
    text = state.get("input_text", "").strip()
    return {
        "input_text": text,
        "current_step": "normalize_input",
        "steps_completed": state.get("steps_completed", []) + ["normalize_input"],
        "errors": state.get("errors", []),
    }


async def classify_intent(state: SupportAgentState) -> dict[str, Any]:
    """Classify the intent of the support ticket."""
    router = get_model_router()
    text = state.get("input_text", "")

    prompt = f"""Classify the intent of this support message.

Message: {text}

Return a JSON object with:
- "intent": one of [
  "refund_request", "product_issue", "billing_inquiry", "account_issue",
  "general_inquiry", "escalation", "feedback", "data_request"
]
- "confidence": a float between 0.0 and 1.0

Only return the JSON object."""

    try:
        result = await router.complete_json(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are a support ticket classifier. Return only valid JSON.",
                temperature=0.1,
                max_tokens=100,
            ),
            purpose=TaskPurpose.CLASSIFICATION,
        )
        return {
            "intent": result.get("intent", "general_inquiry"),
            "intent_confidence": float(result.get("confidence", 0.5)),
            "current_step": "classify_intent",
            "steps_completed": state.get("steps_completed", []) + ["classify_intent"],
        }
    except Exception as exc:
        logger.warning("classify_intent_falling_back", error=str(exc))
        try:
            from app.tools.mock_tools import ClassifyTicketInput, classify_ticket

            fallback = classify_ticket(ClassifyTicketInput(text=text, source="agent_fallback"))
            intent = _support_intent(fallback.intent)
            confidence = fallback.confidence
        except Exception:
            intent = "general_inquiry"
            confidence = 0.0
        return {
            "intent": intent,
            "intent_confidence": confidence,
            "current_step": "classify_intent",
            "steps_completed": state.get("steps_completed", []) + ["classify_intent"],
        }


async def detect_priority(state: SupportAgentState) -> dict[str, Any]:
    """Detect the priority level of the ticket."""
    router = get_model_router()
    text = state.get("input_text", "")
    intent = state.get("intent", "general_inquiry")

    prompt = f"""Determine the priority of this support message.

Message: {text}
Detected intent: {intent}

Return a JSON object with:
- "priority": one of ["low", "normal", "high", "urgent"]
- "reason": brief explanation for the priority level

Only return the JSON object."""

    try:
        result = await router.complete_json(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are a priority classifier. Return only valid JSON.",
                temperature=0.1,
                max_tokens=150,
            ),
            purpose=TaskPurpose.CLASSIFICATION,
        )
        return {
            "priority": result.get("priority", "normal"),
            "current_step": "detect_priority",
            "steps_completed": state.get("steps_completed", []) + ["detect_priority"],
        }
    except Exception as exc:
        logger.warning("detect_priority_falling_back", error=str(exc))
        try:
            from app.tools.mock_tools import DetectPriorityInput
            from app.tools.mock_tools import detect_priority as detect

            fallback = detect(DetectPriorityInput(text=text, intent=intent))
            priority = fallback.priority
        except Exception:
            priority = "normal"
        return {
            "priority": priority,
            "current_step": "detect_priority",
            "steps_completed": state.get("steps_completed", []) + ["detect_priority"],
        }


async def extract_entities(state: SupportAgentState) -> dict[str, Any]:
    """Extract structured entities from the message."""
    router = get_model_router()
    text = state.get("input_text", "")

    prompt = f"""Extract structured entities from this support message.

Message: {text}

Return a JSON object with the following fields (use null for missing):
- "customer_name": string or null
- "customer_email": string or null
- "order_id": string or null
- "product": string or null
- "issue_type": string or null
- "dates": list of date strings or empty list
- "amounts": list of monetary amounts or empty list

Only return the JSON object."""

    try:
        result = await router.complete_json(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are an entity extractor. Return only valid JSON.",
                temperature=0.0,
                max_tokens=300,
            ),
            purpose=TaskPurpose.EXTRACTION,
        )
        return {
            "entities": result,
            "current_step": "extract_entities",
            "steps_completed": state.get("steps_completed", []) + ["extract_entities"],
        }
    except Exception as exc:
        logger.error("extract_entities_failed", error=str(exc))
        return {
            "entities": {},
            "current_step": "extract_entities",
            "errors": state.get("errors", []) + [f"extract_entities: {exc}"],
            "steps_completed": state.get("steps_completed", []) + ["extract_entities"],
        }


async def retrieve_policy_context(state: SupportAgentState) -> dict[str, Any]:
    """Retrieve relevant policy context from the knowledge base."""
    from app.core.database import async_session_factory
    from app.retrieval.context import pack_context
    from app.retrieval.reranker import rerank_results
    from app.retrieval.search import hybrid_search

    text = state.get("input_text", "")
    intent = state.get("intent", "")
    query = f"{intent}: {text}"

    try:
        async with async_session_factory()() as session:
            results = await hybrid_search(session, query, limit=20)
            reranked = await rerank_results(query, results, top_k=5)
            packed = pack_context(reranked)

            return {
                "retrieved_context": packed.context_text,
                "citations": [
                    {
                        "index": c.index,
                        "title": c.document_title,
                        "heading": c.heading,
                    }
                    for c in packed.citations
                ],
                "current_step": "retrieve_policy_context",
                "steps_completed": state.get("steps_completed", [])
                + ["retrieve_policy_context"],
            }
    except Exception as exc:
        logger.warning("retrieve_context_failed", error=str(exc))
        return {
            "retrieved_context": "",
            "citations": [],
            "current_step": "retrieve_policy_context",
            "errors": state.get("errors", [])
            + [f"retrieve_policy_context: {exc}"],
            "steps_completed": state.get("steps_completed", [])
            + ["retrieve_policy_context"],
        }


async def draft_response(state: SupportAgentState) -> dict[str, Any]:
    """Generate a customer-facing draft response."""
    router = get_model_router()
    text = state.get("input_text", "")
    intent = state.get("intent", "general_inquiry")
    priority = state.get("priority", "normal")
    entities = state.get("entities", {})
    context = state.get("retrieved_context", "")

    system = """You are a professional customer support agent. Draft a helpful, 
empathetic response to the customer. Use the retrieved policy context to inform 
your response. Do NOT promise refunds or irreversible actions directly. Instead,
mention that such requests will be reviewed by a team member.

Keep the response concise and professional."""

    prompt = f"""Customer message: {text}

Detected intent: {intent}
Priority: {priority}
Extracted entities: {json.dumps(entities)}

Retrieved policy context:
{context or "No relevant policy found."}

Draft a response to the customer:"""

    try:
        response = await router.complete(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt=system,
                temperature=0.4,
                max_tokens=500,
            ),
            purpose=TaskPurpose.DRAFTING,
        )
        return {
            "draft_response": response.content,
            "current_step": "draft_response",
            "steps_completed": state.get("steps_completed", []) + ["draft_response"],
        }
    except Exception as exc:
        logger.error("draft_response_failed", error=str(exc))
        return {
            "draft_response": "",
            "current_step": "draft_response",
            "errors": state.get("errors", []) + [f"draft_response: {exc}"],
            "steps_completed": state.get("steps_completed", []) + ["draft_response"],
        }


async def plan_tool_actions(state: SupportAgentState) -> dict[str, Any]:
    """Plan which tool actions to execute based on the analysis."""
    router = get_model_router()
    intent = state.get("intent", "general_inquiry")
    entities = state.get("entities", {})
    draft = state.get("draft_response", "")

    available_tools = sorted(SUPPORT_ACTION_TOOLS)

    prompt = f"""Based on this support ticket analysis, plan which tool actions 
should be executed.

Intent: {intent}
Entities: {json.dumps(entities)}
Draft response: {draft[:300]}

Available tools: {json.dumps(available_tools)}

Return a JSON object with:
- "actions": a list of objects, each with:
  - "tool_name": name of the tool
  - "payload": the input parameters for the tool
  - "reason": why this action is needed

Only propose tools that produce an operational side effect after analysis.
Do not propose classification, priority detection, extraction, or knowledge
search tools here because those steps already ran earlier in the workflow."""

    try:
        result = await router.complete_json(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are a tool planner. Return only valid JSON.",
                temperature=0.2,
                max_tokens=800,
            ),
            purpose=TaskPurpose.ROUTING,
        )
        actions = _normalize_planned_actions(result.get("actions", []), state)
        return {
            "planned_actions": actions,
            "current_step": "plan_tool_actions",
            "steps_completed": state.get("steps_completed", [])
            + ["plan_tool_actions"],
        }
    except Exception as exc:
        logger.error("plan_tool_actions_failed", error=str(exc))
        actions = _normalize_planned_actions([], state)
        return {
            "planned_actions": actions,
            "current_step": "plan_tool_actions",
            "errors": state.get("errors", []) + [f"plan_tool_actions: {exc}"],
            "steps_completed": state.get("steps_completed", [])
            + ["plan_tool_actions"],
        }


async def policy_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Classify each planned action through the guardrail policy engine."""
    from app.guardrails.policy import PolicyAction, PolicyEngine
    from app.tools.registry import tool_registry

    engine = PolicyEngine()
    planned = state.get("planned_actions") or state.get("plan") or []

    safe: list[dict] = []
    approval_required: list[dict] = []
    blocked: list[dict] = []

    for action in planned:
        tool_name = action.get("tool_name", "")
        decision = engine.decide(
            registry=tool_registry,
            tool_name=tool_name,
            payload=action.get("payload", {}),
        )

        action_with_decision = {**action}

        if decision.action == PolicyAction.ALLOW:
            action_with_decision["policy_decision"] = "safe"
            safe.append(action_with_decision)
        elif decision.action == PolicyAction.REQUEST_APPROVAL:
            action_with_decision["policy_decision"] = "approval_required"
            approval_required.append(action_with_decision)
        elif decision.action == PolicyAction.DENY:
            action_with_decision["policy_decision"] = "blocked"
            blocked.append(action_with_decision)

    logger.info(
        "policy_gate_complete",
        safe=len(safe),
        approval_required=len(approval_required),
        blocked=len(blocked),
    )

    return {
        "safe_actions": safe,
        "approval_required_actions": approval_required,
        "blocked_actions": blocked,
        "current_step": "policy_gate",
        "steps_completed": state.get("steps_completed", []) + ["policy_gate"],
    }


async def execute_safe_tools(state: dict[str, Any]) -> dict[str, Any]:
    """Execute tools classified as safe."""
    import uuid

    from app.core.database import async_session_factory
    from app.tools.executor import ToolExecutor

    executor = ToolExecutor()
    safe_actions = state.get("safe_actions", [])
    results: list[dict] = state.get("tool_results", [])
    run_id = uuid.UUID(state["run_id"])

    async_session = async_session_factory()
    async with async_session() as session:
        for action in safe_actions:
            tool_name = action.get("tool_name", "")
            payload = action.get("payload", {})

            try:
                result = await executor.execute(
                    session=session,
                    agent_run_id=run_id,
                    tool_name=tool_name,
                    payload=payload,
                    actor_id="agent",
                )
                results.append({
                    "tool_name": tool_name,
                    "status": "completed",
                    "result": result.output_payload,
                })
            except Exception as exc:
                results.append({
                    "tool_name": tool_name,
                    "status": "failed",
                    "error": str(exc),
                })
        await session.commit()

    return {
        "tool_results": results,
        "current_step": "execute_safe_tools",
        "steps_completed": state.get("steps_completed", [])
        + ["execute_safe_tools"],
    }


async def create_approval_requests(state: dict[str, Any]) -> dict[str, Any]:
    """Create approval requests for actions that require human approval."""
    import uuid

    from app.core.database import async_session_factory
    from app.tools.executor import ToolExecutor

    approval_actions = state.get("approval_required_actions", [])
    approval_requests: list[dict] = []
    run_id = uuid.UUID(state["run_id"])

    executor = ToolExecutor()
    async_session = async_session_factory()
    async with async_session() as session:
        for action in approval_actions:
            tool_name = action.get("tool_name", "")
            payload = action.get("payload", {})
            reason = action.get("reason", "")

            try:
                result = await executor.execute(
                    session=session,
                    agent_run_id=run_id,
                    tool_name=tool_name,
                    payload=payload,
                    actor_id="agent",
                    require_approval=True,
                )
                if result.approval_request_id:
                    approval_requests.append({
                        "id": str(result.approval_request_id),
                        "tool_name": tool_name,
                        "payload": payload,
                        "reason": reason,
                        "status": "pending_review",
                    })
            except Exception as exc:
                logger.error("create_approval_request_failed", tool_name=tool_name, error=str(exc))

        await session.commit()

    logger.info(
        "approval_requests_created",
        count=len(approval_requests),
    )

    return {
        "approval_requests": approval_requests,
        "current_step": "create_approval_requests",
        "steps_completed": state.get("steps_completed", [])
        + ["create_approval_requests"],
    }


async def execute_approved_tools(state: dict[str, Any]) -> dict[str, Any]:
    """Execute tools that have been approved by a human reviewer."""
    import uuid

    from app.core.database import async_session_factory
    from app.tools.executor import ToolExecutor

    executor = ToolExecutor()
    approved = state.get("approved_actions", [])
    results: list[dict] = state.get("tool_results", [])
    run_id = uuid.UUID(state["run_id"])

    async_session = async_session_factory()
    async with async_session() as session:
        for action in approved:
            tool_name = action.get("tool_name", "")
            payload = action.get("payload", {})

            try:
                result = await executor.execute(
                    session=session,
                    agent_run_id=run_id,
                    tool_name=tool_name,
                    payload=payload,
                    actor_id="system",
                )
                results.append({
                    "tool_name": tool_name,
                    "status": "completed",
                    "result": result.output_payload,
                    "approved": True,
                })
            except Exception as exc:
                results.append({
                    "tool_name": tool_name,
                    "status": "failed",
                    "error": str(exc),
                    "approved": True,
                })
        await session.commit()

    return {
        "tool_results": results,
        "current_step": "execute_approved_tools",
        "steps_completed": state.get("steps_completed", [])
        + ["execute_approved_tools"],
    }


async def finalize_output(state: SupportAgentState) -> dict[str, Any]:
    """Compile the final output from all completed steps."""
    draft = state.get("draft_response", "")
    tool_results = state.get("tool_results", [])
    approval_requests = state.get("approval_requests", [])
    planned_actions = state.get("planned_actions", [])
    blocked = state.get("blocked_actions", [])
    errors = state.get("errors", [])

    completed = [result for result in tool_results if result.get("status") == "completed"]
    email_actions = [
        action
        for action in planned_actions
        if action.get("tool_name") == "send_email"
    ]
    pending_email = next(iter(email_actions), None)

    if approval_requests:
        summary = "Draft is ready and a sensitive action is waiting for human approval."
    elif completed:
        summary = f"Completed {len(completed)} safe action(s)."
    elif blocked:
        summary = "Some actions were blocked by policy."
    elif errors:
        summary = "The agent finished with recoverable errors."
    else:
        summary = "The agent prepared a response without executing tools."

    return {
        "final_output": {
            "summary": summary,
            "draft_response": draft or None,
            "planned_actions": planned_actions,
            "tool_results": tool_results,
            "approvals": approval_requests,
            "pending_email": pending_email,
            "blocked_actions": blocked,
            "errors": errors,
            "counts": {
                "planned_actions": len(planned_actions),
                "tool_results": len(tool_results),
                "pending_approvals": len(approval_requests),
                "blocked_actions": len(blocked),
                "errors": len(errors),
            },
        },
        "current_step": "finalize_output",
        "steps_completed": state.get("steps_completed", []) + ["finalize_output"],
    }


# ── Workflow Automation Nodes ────────────────────────────────────────


async def parse_instruction(state: WorkflowAutomationState) -> dict[str, Any]:
    """Parse the workflow instruction."""
    text = state.get("input_text", "").strip()
    return {
        "instruction": text,
        "current_step": "parse_instruction",
        "steps_completed": state.get("steps_completed", []) + ["parse_instruction"],
    }


async def generate_plan(state: WorkflowAutomationState) -> dict[str, Any]:
    """Generate an execution plan from the instruction."""
    router = get_model_router()
    instruction = state.get("instruction", "")

    available_tools = [
        "summarize_tickets",
        "generate_report",
        "export_report",
        "search_knowledge_base",
    ]

    prompt = f"""Create an execution plan for this instruction:

Instruction: {instruction}

Available tools: {json.dumps(available_tools)}

Return a JSON object with:
- "plan": a list of step objects, each with:
  - "step": step number
  - "tool_name": name of the tool to call
  - "payload": input parameters
  - "description": what this step does

Only return the JSON object."""

    try:
        result = await router.complete_json(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are a workflow planner. Return only valid JSON.",
                temperature=0.2,
                max_tokens=800,
            ),
            purpose=TaskPurpose.ROUTING,
        )
        return {
            "plan": result.get("plan", []),
            "current_step": "generate_plan",
            "steps_completed": state.get("steps_completed", []) + ["generate_plan"],
        }
    except Exception as exc:
        return {
            "plan": [],
            "current_step": "generate_plan",
            "errors": state.get("errors", []) + [f"generate_plan: {exc}"],
            "steps_completed": state.get("steps_completed", []) + ["generate_plan"],
        }


async def generate_final_report(state: WorkflowAutomationState) -> dict[str, Any]:
    """Generate a final report from the workflow results."""
    router = get_model_router()
    instruction = state.get("instruction", "")
    tool_results = state.get("tool_results", [])

    prompt = f"""Generate a summary report for this completed workflow.

Original instruction: {instruction}
Tool results: {json.dumps(tool_results[:5])}

Write a clear, concise report summarizing what was accomplished."""

    try:
        response = await router.complete(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model="",
                system_prompt="You are a report writer. Write clear, structured reports.",
                temperature=0.3,
                max_tokens=1000,
            ),
            purpose=TaskPurpose.DRAFTING,
        )
        return {
            "final_report": response.content,
            "current_step": "generate_final_report",
            "steps_completed": state.get("steps_completed", [])
            + ["generate_final_report"],
        }
    except Exception as exc:
        return {
            "final_report": f"Report generation failed: {exc}",
            "current_step": "generate_final_report",
            "errors": state.get("errors", []) + [f"generate_final_report: {exc}"],
            "steps_completed": state.get("steps_completed", [])
            + ["generate_final_report"],
        }
