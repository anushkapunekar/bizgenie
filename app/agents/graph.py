"""
LangGraph wrapper with a single answer node.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.agents.nodes.rag import generate_answer
from app.tools.calendar_mcp import create_event
from app.tools.email_mcp import send_email
from app.tools.whatsapp_mcp import send_whatsapp_message

logger = structlog.get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_message: str
    business_id: int
    business_context: Dict[str, Any]
    response: str
    documents_used: int
    tool_actions: list


def _schedule_tool(coro):
    """Schedule async tool execution without blocking."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = loop.create_task(coro)
        else:
            task = loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
        return

    def _on_done(fut: asyncio.Future):
        try:
            result = fut.result()
            logger.info("agent.tool_completed", result=result)
        except Exception as exc:  # pragma: no cover
            logger.error("agent.tool_failed", error=str(exc))

    task.add_done_callback(_on_done)


def tool_router(reply: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspect LLM output; if it contains call_tool instructions, execute tool.
    Expected JSON format:
    {
        "answer": "...",
        "call_tool": {
            "name": "send_whatsapp",
            "params": {...}
        }
    }
    """
    data: Optional[Dict[str, Any]] = None
    trimmed = reply.strip()
    if trimmed.startswith("{") and trimmed.endswith("}"):
        try:
            data = json.loads(trimmed)
        except json.JSONDecodeError:
            data = None

    if not data or "call_tool" not in data:
        return {"reply": reply, "tool_actions": []}

    call = data["call_tool"]
    tool_name = call.get("name")
    params = call.get("params", {})
    tool_actions = []

    if tool_name == "send_whatsapp":
        to = params.get("to") or business_context.get("contact_phone")
        message = params.get("message") or data.get("answer", reply)
        if to and message:
            logger.info("agent.tool_trigger", tool=tool_name, to=to)
            _schedule_tool(send_whatsapp_message(to=to, message=message))
            tool_actions.append({"tool": "whatsapp", "to": to})
    elif tool_name == "send_email":
        to = params.get("to") or business_context.get("contact_email")
        subject = params.get("subject") or "Notification from BizGenie"
        body = params.get("body") or data.get("answer", reply)
        if to and body:
            logger.info("agent.tool_trigger", tool=tool_name, to=to)
            _schedule_tool(send_email(to=to, subject=subject, body=body))
            tool_actions.append({"tool": "email", "to": to})
    elif tool_name == "create_event":
        logger.info("agent.tool_trigger", tool=tool_name)
        _schedule_tool(
            create_event(
                title=params.get("title", "BizGenie Event"),
                start_dt=params.get("start_dt"),
                end_dt=params.get("end_dt"),
                description=params.get("description", ""),
                attendees_emails=params.get("attendees_emails", []),
                location=params.get("location"),
                send_via_email=params.get("send_via_email", True),
                send_via_whatsapp=params.get("send_via_whatsapp", False),
            )
        )
        tool_actions.append({"tool": "calendar"})

    final_reply = data.get("answer", reply)
    return {"reply": final_reply, "tool_actions": tool_actions}


def answer_node(state: AgentState) -> AgentState:
    user_message = state["user_message"]
    business_id = state["business_id"]
    business_ctx = state.get("business_context") or {}

    result = generate_answer(
        business_id=business_id,
        user_message=user_message,
        metadata_context=business_ctx,
    )

    routed = tool_router(result["reply"], business_ctx)
    state["response"] = routed["reply"]
    state["documents_used"] = result["documents_used"]
    state["tool_actions"] = routed.get("tool_actions", [])
    logger.info(
        "agent.response_ready",
        business_id=business_id,
        documents_used=result["documents_used"],
        tools_triggered=len(state["tool_actions"]),
    )
    return state


workflow = StateGraph(AgentState)
workflow.add_node("answer", answer_node)
workflow.set_entry_point("answer")
workflow.add_edge("answer", END)

agent_graph = workflow.compile()


def run_agent(*, business_id: int, user_message: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
    initial_state: AgentState = {
        "business_id": business_id,
        "user_message": user_message,
        "business_context": business_context,
    }
    final_state = agent_graph.invoke(initial_state)
    return {
        "reply": final_state["response"],
        "documents_used": final_state.get("documents_used", 0),
        "tool_actions": final_state.get("tool_actions", []),
    }