"""Workflow automation LangGraph workflow."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    create_approval_requests,
    execute_approved_tools,
    execute_safe_tools,
    generate_final_report,
    generate_plan,
    parse_instruction,
    policy_gate,
)
from app.agents.state import WorkflowAutomationState


def _has_approval_actions(state: WorkflowAutomationState) -> str:
    """Route based on whether there are approval-required actions."""
    if state.get("approval_required_actions"):
        return "create_approval_requests"
    return "generate_final_report"


def build_workflow_graph() -> StateGraph:
    """Build the workflow automation LangGraph workflow.

    Flow:
    parse_instruction -> generate_plan -> policy_gate -> execute_safe_tools
    -> [conditional]
       -> create_approval_requests (if needed)
       -> generate_final_report (if no approvals needed)

    After approval (resumed):
    -> execute_approved_tools -> generate_final_report
    """
    graph = StateGraph(WorkflowAutomationState)

    graph.add_node("parse_instruction", parse_instruction)
    graph.add_node("generate_plan", generate_plan)
    graph.add_node("policy_gate", policy_gate)
    graph.add_node("execute_safe_tools", execute_safe_tools)
    graph.add_node("create_approval_requests", create_approval_requests)
    graph.add_node("execute_approved_tools", execute_approved_tools)
    graph.add_node("generate_final_report", generate_final_report)

    graph.set_entry_point("parse_instruction")

    graph.add_edge("parse_instruction", "generate_plan")
    graph.add_edge("generate_plan", "policy_gate")
    graph.add_edge("policy_gate", "execute_safe_tools")

    graph.add_conditional_edges(
        "execute_safe_tools",
        _has_approval_actions,
        {
            "create_approval_requests": "create_approval_requests",
            "generate_final_report": "generate_final_report",
        },
    )

    graph.add_edge("create_approval_requests", END)

    graph.add_edge("execute_approved_tools", "generate_final_report")
    graph.add_edge("generate_final_report", END)

    return graph
