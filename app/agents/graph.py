"""
LangGraph wrapper (SINGLE NODE FIXED)
"""

from __future__ import annotations
import asyncio
import json
from typing import Any, Dict, TypedDict

import structlog
from langgraph.graph import END, StateGraph
from app.agents.nodes.rag import generate_answer

# Tools
from app.tools.calendar_mcp import create_event, update_event, cancel_event
from app.tools.email_mcp import (
    send_email, send_email_confirmation, send_email_update,
    send_email_cancellation, send_email_reminder, send_email_followup
)
from app.tools.whatsapp_mcp import (
    send_whatsapp_message, send_whatsapp_confirmation,
    send_whatsapp_update, send_whatsapp_cancellation,
    send_whatsapp_followup
)

logger = structlog.get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_message: str
    business_id: int
    business_context: Dict[str, Any]
    response: str
    documents_used: int
    tool_actions: list


def _schedule_tool(coro):
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)
        task.add_done_callback(lambda fut: None)
    except RuntimeError:
        pass


def tool_router(reply: str, business_context: Dict[str, Any]):
    """Parses JSON replies. Falls back to plain text."""
    try:
        data = json.loads(reply)
    except:
        return {"reply": reply, "tool_actions": []}

    call = data.get("call_tool")
    if not call:
        return {"reply": data.get("answer", reply), "tool_actions": []}

    name = call.get("name")
    params = call.get("params", {})
    actions = []

    # WhatsApp tools
    if name == "send_whatsapp":
        to = params.get("to") or business_context.get("contact_phone")
        msg = params.get("message") or data.get("answer")
        if to and msg:
            _schedule_tool(send_whatsapp_message(to=to, message=msg))
            actions.append({"tool": "whatsapp", "action": "send_whatsapp"})

    elif name == "send_whatsapp_confirmation":
        _schedule_tool(send_whatsapp_confirmation(**params))
        actions.append({"tool": "whatsapp", "action": "confirmation"})

    elif name == "send_whatsapp_update":
        _schedule_tool(send_whatsapp_update(**params))
        actions.append({"tool": "whatsapp", "action": "update"})

    elif name == "send_whatsapp_cancellation":
        _schedule_tool(send_whatsapp_cancellation(**params))
        actions.append({"tool": "whatsapp", "action": "cancel"})

    elif name == "send_whatsapp_followup":
        _schedule_tool(send_whatsapp_followup(**params))
        actions.append({"tool": "whatsapp", "action": "followup"})

    # Email tools
    elif name == "send_email":
        to = params.get("to") or business_context.get("contact_email")
        subject = params.get("subject") or "BizGenie Notification"
        body = params.get("body") or data.get("answer")
        if to and body:
            _schedule_tool(send_email(to=to, subject=subject, body=body))
            actions.append({"tool": "email", "action": "send_email"})

    elif name == "send_email_confirmation":
        _schedule_tool(send_email_confirmation(**params))
        actions.append({"tool": "email", "action": "confirmation"})

    elif name == "send_email_update":
        _schedule_tool(send_email_update(**params))
        actions.append({"tool": "email", "action": "update"})

    elif name == "send_email_cancellation":
        _schedule_tool(send_email_cancellation(**params))
        actions.append({"tool": "email", "action": "cancel"})

    elif name == "send_email_reminder":
        _schedule_tool(send_email_reminder(**params))
        actions.append({"tool": "email", "action": "reminder"})

    elif name == "send_email_followup":
        _schedule_tool(send_email_followup(**params))
        actions.append({"tool": "email", "action": "followup"})

    # Calendar tools
    elif name == "create_event":
        _schedule_tool(create_event(**params))
        actions.append({"tool": "calendar", "action": "create"})

    elif name == "update_event":
        _schedule_tool(update_event(**params))
        actions.append({"tool": "calendar", "action": "update"})

    elif name == "cancel_event":
        _schedule_tool(cancel_event(**params))
        actions.append({"tool": "calendar", "action": "cancel"})

    final_reply = data.get("answer", reply)
    return {"reply": final_reply, "tool_actions": actions}


def answer_node(state: AgentState) -> AgentState:
    user_message = state["user_message"]
    business_id = state["business_id"]
    ctx = state["business_context"]

    result = generate_answer(
        business_id=business_id,
        user_message=user_message,
        metadata_context=ctx
    )

    routed = tool_router(result["reply"], ctx)

    state["response"] = routed["reply"] or ""
    state["tool_actions"] = routed.get("tool_actions") or []
    state["documents_used"] = result.get("documents_used", 0)

    return state


workflow = StateGraph(AgentState)
workflow.add_node("answer", answer_node)
workflow.set_entry_point("answer")
workflow.add_edge("answer", END)

agent_graph = workflow.compile()


def run_agent(*, business_id: int, user_message: str, business_context: Dict[str, Any]):
    initial: AgentState = {
        "business_id": business_id,
        "user_message": user_message,
        "business_context": business_context,
        "response": "",
        "documents_used": 0,
        "tool_actions": []
    }

    return agent_graph.invoke(initial)
