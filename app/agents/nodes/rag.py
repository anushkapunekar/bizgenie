"""
BizGenie RAG + Tool Reasoning Layer — FINAL VERSION

- Answers FAQs with LLM + vector store
- Detects appointment / WhatsApp intents
- For clear booking requests with date+time → returns JSON tool call for create_event
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json
import re

import structlog

from app.llm_service import llm_service
from app.rag.vectorstore import vector_store

logger = structlog.get_logger(__name__)

# -----------------------------
#   INTENT & DATE/TIME HELPERS
# -----------------------------

BOOKING_KEYWORDS = [
    "book", "appointment", "schedule", "slot", "reserve",
    "reschedule", "cancel my appointment", "change my appointment",
    "confirm appointment", "book an appointment", "fix an appointment",
]

WHATSAPP_KEYWORDS = [
    "whatsapp", "send message", "text me", "send me a whatsapp", "whats app"
]


def extract_datetime(user_message: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Very simple extractor:
    - Looks for YYYY-MM-DD
    - Looks for HH:MM (24h)
    Returns (date, time) or (None, None)
    """
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    time_pattern = r"\d{2}:\d{2}"

    date_match = re.search(date_pattern, user_message)
    time_match = re.search(time_pattern, user_message)

    date = date_match.group(0) if date_match else None
    time = time_match.group(0) if time_match else None

    return date, time


def user_wants_tool(user_message: str) -> bool:
    text = user_message.lower()
    return any(k in text for k in BOOKING_KEYWORDS) or any(
        k in text for k in WHATSAPP_KEYWORDS
    )


# -----------------------------
#   DOCUMENT / METADATA HELPERS
# -----------------------------


def _format_documents(documents: List[Dict[str, Any]]) -> str:
    out: List[str] = []
    for idx, doc in enumerate(documents, 1):
        body = (doc.get("text") or "").strip()
        if not body:
            continue
        meta = doc.get("metadata") or {}
        src = meta.get("filename") or meta.get("source") or "Document"
        out.append(f"[{idx}] From {src}:\n{body}")
    return "\n\n".join(out)


def _fallback_from_metadata(question: str, meta: Dict[str, Any]) -> str:
    name = meta.get("name", "this business")
    services = meta.get("services") or []
    hours = meta.get("working_hours") or {}
    email = meta.get("contact_email") or ""
    phone = meta.get("contact_phone") or ""

    ans: List[str] = [f"Here's what I can tell you about {name}:"]

    if services:
        if isinstance(services, list):
            ans.append("\n• Services: " + ", ".join(services))
        else:
            ans.append("\n• Services: " + str(services))

    if hours:
        ans.append("\n• Working hours:")
        for d, h in hours.items():
            if h and h.get("open") and h.get("close"):
                ans.append(f"  - {d.capitalize()}: {h['open']}–{h['close']}")

    if email or phone:
        ans.append("\n• Contact:")
        if email:
            ans.append(f"  - Email: {email}")
        if phone:
            ans.append(f"  - Phone/WhatsApp: {phone}")

    ans.append(f"\nYou asked: “{question}”. I can also help you book an appointment if you share a date and time.")
    return "\n".join(ans)


def _build_prompt(user_message: str, docs: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    docs_block = _format_documents(docs) if docs else "No matching documents."

    return f"""
You are BizGenie, an AI assistant for a small business.

BUSINESS INFO:
{json.dumps(meta, indent=2)}

DOCUMENTS:
{docs_block}

RULES:
1. If the user clearly asks to book / reschedule / cancel / confirm an appointment
   BUT they do NOT provide a specific date and time → DO NOT call tools.
   Instead, ask them to share date and time.

2. If they ask a normal question about services / prices / availability
   → Answer in natural English using the documents and business info.
   DO NOT return JSON in this case.

3. If they ask you to send a WhatsApp message (e.g. "send me a WhatsApp", "send a message on WhatsApp"):
   You MAY respond with JSON like:
   {{
     "answer": "<what you will send>",
     "call_tool": {{
        "name": "send_whatsapp_message",
        "params": {{
           "to": "<phone or leave empty>",
           "message": "<body>"
        }}
     }}
   }}

IMPORTANT:
- Only return JSON when you are SURE a tool should be used.
- Otherwise, return plain English text only.

USER MESSAGE:
{user_message}

Now respond:
"""


# -----------------------------
#   MAIN ENTRY
# -----------------------------


def generate_answer(
    *,
    business_id: int,
    user_message: str,
    n_results: int = 5,
    metadata_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main RAG routine.

    - For clear booking requests **with** a date+time → we build JSON ourselves.
    - For everything else we call the LLM with a careful prompt.
    """
    meta: Dict[str, Any] = metadata_context or {}

    # 1) Try vector store
    try:
        docs = vector_store.query_documents(
            business_id=business_id,
            query=user_message,
            n_results=n_results,
        )
    except Exception as exc:
        logger.error("rag.vectorstore_failed", error=str(exc))
        docs = []

    # 2) Fast path: appointment request with explicit date+time → build JSON directly
    wants_tool = user_wants_tool(user_message)
    date, time = extract_datetime(user_message)

    if wants_tool and date and time:
        # Build ISO-like start datetime
        start_dt = f"{date}T{time}"

        answer_text = (
            f"Great, I’ll book an appointment for you on {date} at {time}. "
            f"You’ll receive a confirmation shortly."
        )

        params: Dict[str, Any] = {
            "title": f"Appointment on {date} at {time}",
            "description": user_message,
            "start_dt": start_dt,
            # Leave end_dt optional → calendar_mcp will choose a reasonable duration
            "location": meta.get("address"),
            "send_via_email": True,
            "send_via_whatsapp": bool(meta.get("contact_phone")),
            # emails / whatsapp_to will be filled in by tool_router using business context
        }

        reply_json = {
            "answer": answer_text,
            "call_tool": {
                "name": "create_event",
                "params": params,
            },
        }

        reply_str = json.dumps(reply_json)
        logger.info(
            "rag.autobook_json_built",
            business_id=business_id,
            start_dt=start_dt,
        )

        return {
            "reply": reply_str,
            "documents_used": len(docs),
            "metadata_context": meta,
        }

    # 3) If they clearly want tools but no date/time → ask for clarification, NO tool call
    if wants_tool and (not date or not time):
        clarification = (
            "I can help you with appointments or WhatsApp messages. "
            "Please share the exact date (YYYY-MM-DD) and time (HH:MM) "
            "you’d like for the appointment, or clarify what you’d like me to send."
        )
        return {
            "reply": clarification,
            "documents_used": len(docs),
            "metadata_context": meta,
        }

    # 4) Normal FAQ / chit-chat → go through LLM
    prompt = _build_prompt(user_message, docs, meta)

    try:
        reply = llm_service.generate(prompt).strip()
    except Exception as exc:
        logger.error("rag.llm_failed", error=str(exc))
        reply = ""

    if not reply:
        # final safety net
        reply = _fallback_from_metadata(user_message, meta)

    return {
        "reply": reply,
        "documents_used": len(docs),
        "metadata_context": meta,
    }
