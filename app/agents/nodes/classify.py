"""
Advanced intent classification for BizGenie agent.
Expanded to support detailed appointment and tool actions.
Old logic preserved at bottom for reference.
"""

from typing import Dict, Any, Literal
import structlog

logger = structlog.get_logger(__name__)


def classify_intent(
    user_message: str,
    business_context: Dict[str, Any]
) -> Literal[
    "create_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    "appointment_status",
    "appointment_reminder",
    "follow_up",
    "general_tools",
    "faq",
    "rag"
]:
    """
    Advanced intent classifier.
    Detects detailed appointment and tool-related intents.
    """

    msg = user_message.lower().strip()

    # -----------------------------
    # Appointment → Create
    # -----------------------------
    create_keywords = [
        "book", "schedule", "appointment", "reserve",
        "slot", "available", "can i come", "can we meet",
        "want to book", "consultation", "meeting"
    ]
    if any(k in msg for k in create_keywords):
        logger.info("Intent classified as create_appointment", msg=user_message[:50])
        return "create_appointment"

    # -----------------------------
    # Appointment → Cancel
    # -----------------------------
    cancel_keywords = [
        "cancel", "call off", "don't want", "remove my booking",
        "no longer need", "cancel my appointment"
    ]
    if any(k in msg for k in cancel_keywords):
        logger.info("Intent classified as cancel_appointment", msg=user_message[:50])
        return "cancel_appointment"

    # -----------------------------
    # Appointment → Reschedule
    # -----------------------------
    reschedule_keywords = [
        "reschedule", "change time", "shift appointment",
        "move meeting", "another time", "different time"
    ]
    if any(k in msg for k in reschedule_keywords):
        logger.info("Intent classified as reschedule_appointment", msg=user_message[:50])
        return "reschedule_appointment"

    # -----------------------------
    # Appointment → Status Inquiry
    # -----------------------------
    status_keywords = [
        "when is my appointment", "do i have an appointment",
        "appointment status", "what time is my appointment",
        "my slot", "my booking"
    ]
    if any(k in msg for k in status_keywords):
        logger.info("Intent classified as appointment_status", msg=user_message[:50])
        return "appointment_status"

    # -----------------------------
    # Appointment → Reminder
    # -----------------------------
    reminder_keywords = [
        "remind me", "send reminder", "reminder", "notify me before",
        "tell me before"
    ]
    if any(k in msg for k in reminder_keywords):
        logger.info("Intent classified as appointment_reminder", msg=user_message[:50])
        return "appointment_reminder"

    # -----------------------------
    # Tools → Follow-up
    # -----------------------------
    followup_keywords = [
        "follow up", "message them again", "ask again",
        "ping", "contact again"
    ]
    if any(k in msg for k in followup_keywords):
        logger.info("Intent classified as follow_up", msg=user_message[:50])
        return "follow_up"

    # -----------------------------
    # Tools → General Tools
    # -----------------------------
    general_tool_keywords = [
        "send email", "send whatsapp", "notify", "contact",
        "send message", "email them", "whatsapp them"
    ]
    if any(k in msg for k in general_tool_keywords):
        logger.info("Intent classified as general_tools", msg=user_message[:50])
        return "general_tools"

    # -----------------------------
    # FAQ (simple, short questions)
    # -----------------------------
    faq_keywords = [
        "what is", "who are", "where is", "how much",
        "price", "cost", "hours", "open", "closed",
        "contact", "phone", "address"
    ]
    if any(k in msg for k in faq_keywords) and len(msg.split()) < 15:
        logger.info("Intent classified as faq", msg=user_message[:50])
        return "faq"

    # -----------------------------
    # Default → RAG
    # -----------------------------
    logger.info("Intent classified as rag", msg=user_message[:50])
    return "rag"


def classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for intent classification.
    Updated to set detailed intents in agent state.
    """
    user_message = state.get("user_message", "")
    business_context = state.get("business_context", {})

    intent = classify_intent(user_message, business_context)

    state["intent"] = intent
    # state["next_node"] = intent  # for future multi-node workflows

    logger.info("Intent classification completed", intent=intent)

    return state


# ------------------------------------------------
# OLD LOGIC (kept for reference as requested)
# ------------------------------------------------
#
# def classify_intent(user_message: str, business_context: Dict[str, Any]) -> Literal["faq", "rag", "appointment", "tools"]:
#     message_lower = user_message.lower()
#     appointment_keywords = [...]
#     tools_keywords = [...]
#     faq_keywords = [...]
#     if any(...):
#         return "appointment"
#     if any(...):
#         return "tools"
#     if any(...):
#         return "faq"
#     return "rag"
#
