"""
Tools executor node for running MCP tools via the JSON `call_tool` protocol.

Instead of calling WhatsApp / Email / Calendar directly (which are async),
this node *plans* the tool call and encodes it as:

{
  "answer": "...",
  "call_tool": { "name": "...", "params": {...} }
}

Then `tool_router` in `graph.py` actually performs the async work.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
import json
import structlog

logger = structlog.get_logger(__name__)


def extract_tool_requirements(user_message: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a simple tool request from the user's message.

    Returns:
        {
          "tool_name": str | None,   # e.g. "send_whatsapp" | "send_email" | "create_event"
          "params": dict,
          "answer_text": str         # Human-facing confirmation sentence
        }
    """
    msg = user_message.lower()
    params: Dict[str, Any] = {}
    tool_name: Optional[str] = None
    answer_text = "Okay, I'll handle that."

    # Very simple heuristics – you can improve later with LLM-based extraction
    if "whatsapp" in msg or "message" in msg or "text" in msg:
        tool_name = "send_whatsapp"
        params["to"] = business_context.get("contact_phone")
        params["message"] = user_message
        answer_text = "Got it – I’ll send a WhatsApp message for you."

    elif "email" in msg or "mail" in msg:
        tool_name = "send_email"
        params["to"] = business_context.get("contact_email")
        params["subject"] = f"Message from {business_context.get('name', 'BizGenie')} customer"
        params["body"] = user_message
        answer_text = "Got it – I’ll send an email for you."

    elif "appointment" in msg and ("confirm" in msg or "confirmation" in msg or "invite" in msg):
        tool_name = "create_event"
        params["title"] = f"Appointment for {business_context.get('name', 'BizGenie')}"
        # NOTE: In a real system you’d parse actual time, attendees, etc.
        params["start_dt"] = None
        params["end_dt"] = None
        params["description"] = user_message
        params["attendees_emails"] = (
            [business_context.get("contact_email")]
            if business_context.get("contact_email")
            else []
        )
        params["location"] = business_context.get("address")
        params["send_via_email"] = True
        params["send_via_whatsapp"] = False
        answer_text = "I’ll generate an appointment invite for this."

    return {
        "tool_name": tool_name,
        "params": params,
        "answer_text": answer_text,
    }


def tools_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for tool planning.

    - Looks at user_message and business_context
    - Decides which tool to call (if any)
    - Encodes a JSON `call_tool` payload in `state["response"]`
    - Actual execution is handled by `tool_router` in graph.py
    """
    user_message = state.get("user_message", "") or ""
    business_context = state.get("business_context", {}) or {}
    tool_actions = state.get("tool_actions", []) or []

    try:
        extracted = extract_tool_requirements(user_message, business_context)
        tool_name = extracted["tool_name"]
        params = extracted["params"]
        answer_text = extracted["answer_text"]

        if not tool_name:
            # No clear tool intent – ask user for clarification
            state["response"] = (
                "I can send an email, WhatsApp message, or create an appointment invite. "
                "Please tell me which one you want and who it should go to."
            )
            state["tool_actions"] = tool_actions
            return state

        call_tool = {
            "name": tool_name,
            "params": params,
        }

        payload = {
            "answer": answer_text,
            "call_tool": call_tool,
        }

        state["response"] = json.dumps(payload)
        # We *plan* the tool here; graph.tool_router will append the real tool actions
        state["tool_actions"] = tool_actions

        logger.info(
            "tools_executor.planned",
            tool_name=tool_name,
            params=params,
        )

    except Exception as exc:  # pragma: no cover
        logger.error("tools_executor.error", error=str(exc))
        state["response"] = (
            "I encountered an error while preparing that action. "
            "Please try again or contact us directly."
        )

    return state
