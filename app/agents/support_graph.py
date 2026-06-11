"""Support agent LangGraph workflow."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    classify_intent,
    create_approval_requests,
    detect_priority,
    draft_response,
    execute_approved_tools,
    execute_safe_tools,
    extract_entities,
    finalize_output,
    normalize_input,
    plan_tool_actions,
    policy_gate,
    retrieve_policy_context,
)
from app.agents.state import SupportAgentState


def _has_approval_actions(state: SupportAgentState) -> str:
    """Route based on whether there are approval-required actions."""
    if state.get("approval_required_actions"):
        return "create_approval_requests"
    return "finalize_output"


def _has_approved_actions(state: SupportAgentState) -> str:
    """Route based on whether approved actions exist to execute."""
    if state.get("approved_actions"):
        return "execute_approved_tools"
    return "finalize_output"


def build_support_graph() -> StateGraph:
    """Build the support agent LangGraph workflow.

    Flow:
    normalize_input -> classify_intent -> detect_priority -> extract_entities
    -> retrieve_policy_context -> draft_response -> plan_tool_actions
    -> policy_gate -> execute_safe_tools -> [conditional]
       -> create_approval_requests (if approval-required actions exist)
       -> finalize_output (if no approval-required actions)

    After approval (resumed):
    -> execute_approved_tools -> finalize_output
    """
    graph = StateGraph(SupportAgentState)

    # Add nodes.
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("detect_priority", detect_priority)
    graph.add_node("extract_entities", extract_entities)
    graph.add_node("retrieve_policy_context", retrieve_policy_context)
    graph.add_node("draft_response", draft_response)
    graph.add_node("plan_tool_actions", plan_tool_actions)
    graph.add_node("policy_gate", policy_gate)
    graph.add_node("execute_safe_tools", execute_safe_tools)
    graph.add_node("create_approval_requests", create_approval_requests)
    graph.add_node("execute_approved_tools", execute_approved_tools)
    graph.add_node("finalize_output", finalize_output)

    # Set entry point.
    graph.set_entry_point("normalize_input")

    # Linear flow.
    graph.add_edge("normalize_input", "classify_intent")
    graph.add_edge("classify_intent", "detect_priority")
    graph.add_edge("detect_priority", "extract_entities")
    graph.add_edge("extract_entities", "retrieve_policy_context")
    graph.add_edge("retrieve_policy_context", "draft_response")
    graph.add_edge("draft_response", "plan_tool_actions")
    graph.add_edge("plan_tool_actions", "policy_gate")
    graph.add_edge("policy_gate", "execute_safe_tools")

    # Conditional: after safe tools, check if approval is needed.
    graph.add_conditional_edges(
        "execute_safe_tools",
        _has_approval_actions,
        {
            "create_approval_requests": "create_approval_requests",
            "finalize_output": "finalize_output",
        },
    )

    # Approval requests lead to END (workflow pauses for human).
    graph.add_edge("create_approval_requests", END)

    # After human approval, resume with execution.
    graph.add_conditional_edges(
        "execute_approved_tools",
        lambda _: "finalize_output",
        {"finalize_output": "finalize_output"},
    )

    # Final output ends the workflow.
    graph.add_edge("finalize_output", END)

    return graph
