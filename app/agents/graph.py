"""
BizGenie Graph — simple, stable version.

Single node:
- calls RAG generate_answer()
- no tool execution here
"""
from __future__ import annotations

from typing import Any, Dict, TypedDict

import structlog
from langgraph.graph import StateGraph, END

from app.agents.nodes.rag import generate_answer

logger = structlog.get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_message: str
    business_id: int
    business_context: Dict[str, Any]
    response: str
    documents_used: int
    tool_actions: list


def answer_node(state: AgentState) -> AgentState:
    user_message = state["user_message"]
    business_id = state["business_id"]
    ctx = state["business_context"]

    result = generate_answer(
        business_id=business_id,
        user_message=user_message,
        metadata_context=ctx,
    )

    state["response"] = result.get("reply", "").strip()
    state["documents_used"] = result.get("documents_used", 0)
    state["tool_actions"] = []  # tools triggered only via appointments API now

    logger.info(
        "agent.answer_completed",
        business_id=business_id,
        documents_used=state["documents_used"],
    )

    return state


graph = StateGraph(AgentState)
graph.add_node("answer", answer_node)
graph.set_entry_point("answer")
graph.add_edge("answer", END)
agent_graph = graph.compile()


def run_agent(*, business_id: int, user_message: str, business_context: Dict[str, Any]):
    initial: AgentState = {
        "business_id": business_id,
        "user_message": user_message,
        "business_context": business_context,
    }
    return agent_graph.invoke(initial)
