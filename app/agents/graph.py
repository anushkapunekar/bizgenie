"""
BizGenie Graph — FINAL TOOL-AWARE VERSION

- Single 'answer' node
- Uses RAG node to produce reply (plain text or JSON with call_tool)
- Routes tool calls (calendar, email, WhatsApp)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, TypedDict

import structlog
from langgraph.graph import StateGraph, END

from app.agents.nodes.rag import generate_answer

# Tools
from app.tools.calendar_mcp import create_event, update_event, cancel_event
from app.tools.email_mcp import (
    send_email,
    send_email_confirmation,
    send_email_update,
    send_email_cancellation,
    send_email_reminder,
    send_email_followup,
)
from app.tools.whatsapp_mcp import (
    send_whatsapp_message,
    send_whatsapp_confirmation,
    send_whatsapp_update,
    send_whatsapp_cancellation,
    send_whatsapp_followup,
)

logger = structlog.get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_message: str
    business_id: int
    business_context: Dict[str, Any]
    response: str
    documents_used: int
    tool_actions: List[Dict[str, Any]]


def _schedule(coro, label: str):
    """
    Schedule async tool execution.
    Logs any exceptions instead of silently failing.
    """
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)

        def _done(fut: asyncio.Future):
            try:
                fut.result()
                logger.info("tool.completed", tool=label)
            except Exception as exc:
                logger.error("tool.error", tool=label, error=str(exc))

        task.add_done_callback(_done)
    except RuntimeError as exc:
        logger.error("tool.schedule_failed", tool=label, error=str(exc))


def tool_router(reply: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    If reply is JSON with call_tool, execute the tool in background and
    return {"reply": natural_text, "tool_actions": [...]}.
    Otherwise, treat as plain text.
    """
    try:
        data = json.loads(reply)
    except Exception:
        # Not JSON → plain text
        return {"reply": reply, "tool_actions": []}

    call = data.get("call_tool")
    if not call:
        # JSON but no tool call → just answer
        return {"reply": data.get("answer", reply), "tool_actions": []}

    tool_name = call.get("name")
    params: Dict[str, Any] = call.get("params") or {}
    actions: List[Dict[str, Any]] = []

    if not tool_name:
        return {"reply": data.get("answer", reply), "tool_actions": []}

    # ----------------- WHATSAPP TOOLS -----------------
    if tool_name == "send_whatsapp_message":
        to = params.get("to") or ctx.get("contact_phone")
        message = params.get("message") or data.get("answer")
        if to and message:
            _schedule(
                send_whatsapp_message(to=to, message=message),
                label="send_whatsapp_message",
            )
            actions.append({"tool": "whatsapp", "action": tool_name, "to": to})

    elif tool_name == "send_whatsapp_confirmation":
        _schedule(send_whatsapp_confirmation(**params), label=tool_name)
        actions.append({"tool": "whatsapp", "action": tool_name})

    elif tool_name == "send_whatsapp_update":
        _schedule(send_whatsapp_update(**params), label=tool_name)
        actions.append({"tool": "whatsapp", "action": tool_name})

    elif tool_name == "send_whatsapp_cancellation":
        _schedule(send_whatsapp_cancellation(**params), label=tool_name)
        actions.append({"tool": "whatsapp", "action": tool_name})

    elif tool_name == "send_whatsapp_followup":
        _schedule(send_whatsapp_followup(**params), label=tool_name)
        actions.append({"tool": "whatsapp", "action": tool_name})

    # ----------------- EMAIL TOOLS -----------------
    elif tool_name == "send_email":
        # Fill defaults from business context if missing
        to = params.get("to") or ctx.get("contact_email")
        subject = params.get("subject") or "BizGenie Notification"
        body = params.get("body") or data.get("answer")
        if to and body:
            _schedule(
                send_email(to=to, subject=subject, body=body),
                label="send_email",
            )
            actions.append({"tool": "email", "action": tool_name, "to": to})

    elif tool_name == "send_email_confirmation":
        _schedule(send_email_confirmation(**params), label=tool_name)
        actions.append({"tool": "email", "action": tool_name})

    elif tool_name == "send_email_update":
        _schedule(send_email_update(**params), label=tool_name)
        actions.append({"tool": "email", "action": tool_name})

    elif tool_name == "send_email_cancellation":
        _schedule(send_email_cancellation(**params), label=tool_name)
        actions.append({"tool": "email", "action": tool_name})

    elif tool_name == "send_email_reminder":
        _schedule(send_email_reminder(**params), label=tool_name)
        actions.append({"tool": "email", "action": tool_name})

    elif tool_name == "send_email_followup":
        _schedule(send_email_followup(**params), label=tool_name)
        actions.append({"tool": "email", "action": tool_name})

    # ----------------- CALENDAR TOOLS -----------------
    elif tool_name == "create_event":
        # Fill defaults using business context if missing
        params = dict(params)  # copy
        if params.get("send_via_email") is None:
            params["send_via_email"] = True
        if params.get("send_via_whatsapp") is None:
            params["send_via_whatsapp"] = bool(ctx.get("contact_phone"))

        # attendees_emails
        if "attendees_emails" not in params or not params["attendees_emails"]:
            attendees: List[str] = []
            if ctx.get("contact_email"):
                attendees.append(ctx["contact_email"])
            params["attendees_emails"] = attendees

        # whatsapp_to fallback
        if params.get("send_via_whatsapp") and not params.get("whatsapp_to"):
            if ctx.get("contact_phone"):
                params["whatsapp_to"] = ctx["contact_phone"]

        _schedule(create_event(**params), label="create_event")
        actions.append({"tool": "calendar", "action": "create_event"})

    elif tool_name == "update_event":
        _schedule(update_event(**params), label="update_event")
        actions.append({"tool": "calendar", "action": "update_event"})

    elif tool_name == "cancel_event":
        _schedule(cancel_event(**params), label="cancel_event")
        actions.append({"tool": "calendar", "action": "cancel_event"})

    # If we reach here, we may or may not have actually executed something,
    # but we always return a natural language answer.
    final_reply = data.get("answer") or reply
    return {"reply": final_reply, "tool_actions": actions}


def answer_node(state: AgentState) -> AgentState:
    msg = state["user_message"]
    bid = state["business_id"]
    ctx = state["business_context"]

    result = generate_answer(
        business_id=bid,
        user_message=msg,
        metadata_context=ctx,
    )

    routed = tool_router(result["reply"], ctx)

    state["response"] = routed["reply"] or ""
    state["tool_actions"] = routed.get("tool_actions") or []
    state["documents_used"] = result.get("documents_used") or 0

    return state


# Build graph
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
