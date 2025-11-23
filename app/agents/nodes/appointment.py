"""
Clean Appointment handler for BizGenie (mixed-mode system)

This version:
- Removes old dependency on get_available_slots
- Removes generate_appointment_confirmation (handled via MCP tools now)
- Acts as a conversational appointment planner
- Can return JSON tool calls for calendar event creation
"""
from __future__ import annotations

from typing import Dict, Any
import json
import structlog

logger = structlog.get_logger(__name__)


def extract_appointment_details(user_message: str) -> Dict[str, Any]:
    """
    Simple NLP stub.
    Later we can upgrade with LLM extraction.

    For now, detect only the intent to book & rough time words.
    """
    msg = user_message.lower()

    want_to_book = any(
        word in msg for word in [
            "book", "schedule", "appointment", "reserve", "slot", "meeting"
        ]
    )

    # detect approximate times
    time_keywords = [
        "morning", "evening", "afternoon",
        "tomorrow", "today", "next week", "monday", "tuesday",
        "wednesday", "thursday", "friday", "saturday", "sunday",
    ]
    time_phrase = None
    for t in time_keywords:
        if t in msg:
            time_phrase = t
            break

    return {
        "wants_booking": want_to_book,
        "time_phrase": time_phrase
    }


def appointment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appointment flow:
    - Identify appointment request
    - If user expresses booking intent, suggest tool JSON for create_event
    - Otherwise, ask for date/time details
    """
    user_message = state.get("user_message", "")
    business_context = state.get("business_context", {}) or {}

    extracted = extract_appointment_details(user_message)
    wants_booking = extracted["wants_booking"]
    time_phrase = extracted["time_phrase"]

    business_name = business_context.get("name", "the business")
    contact_email = business_context.get("contact_email")
    contact_phone = business_context.get("contact_phone")

    # -------------------------------
    # CASE 1: User wants to book
    # -------------------------------
    if wants_booking:
        # If user provided some approximate time → auto create an event
        if time_phrase:
            reply = {
                "answer": (
                    f"Okay! I’ll tentatively schedule an appointment "
                    f"({time_phrase}) for you at {business_name}."
                ),
                "call_tool": {
                    "name": "create_event",
                    "params": {
                        "title": f"Appointment ({time_phrase})",
                        "description": user_message,
                        "start_dt": None,  # user didn’t specify
                        "end_dt": None,
                        "location": business_context.get("address"),
                        "attendees_emails": (
                            [contact_email] if contact_email else []
                        ),
                        "send_via_email": True,
                        "send_via_whatsapp": bool(contact_phone),
                    },
                },
            }

            state["response"] = json.dumps(reply)
            logger.info("appointment.autobook", time_phrase=time_phrase)
            return state

        # They want a booking, but no time specified
        state["response"] = (
            "Sure! To book an appointment, please tell me your preferred date and time."
        )
        return state

    # -------------------------------
    # CASE 2: Asking about appointment but not booking
    # -------------------------------
    if "cancel" in user_message.lower():
        state["response"] = (
            "To cancel an appointment, please tell me the date/time of the booking."
        )
        return state

    # -------------------------------
    # DEFAULT fallback
    # -------------------------------
    state["response"] = (
        "I can help you book, reschedule, or cancel an appointment. "
        "Tell me what you'd like to do."
    )

    return state
