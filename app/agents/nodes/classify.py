"""
Intent classification node for the LangGraph agent.
"""
from typing import Dict, Any, Literal
import structlog

logger = structlog.get_logger(__name__)


def classify_intent(user_message: str, business_context: Dict[str, Any]) -> Literal["faq", "rag", "appointment", "tools"]:
    """
    Classify user intent from the message.
    
    Args:
        user_message: User's message
        business_context: Business context information
    
    Returns:
        Intent classification: "faq", "rag", "appointment", or "tools"
    """
    message_lower = user_message.lower()
    
    # Appointment keywords
    appointment_keywords = [
        "appointment", "schedule", "book", "reserve", "available",
        "when can", "what time", "meeting", "consultation"
    ]
    if any(keyword in message_lower for keyword in appointment_keywords):
        logger.info("Intent classified as appointment", message=user_message[:50])
        return "appointment"
    
    # Tools/action keywords
    tools_keywords = [
        "send", "email", "whatsapp", "message", "notify", "contact"
    ]
    if any(keyword in message_lower for keyword in tools_keywords):
        logger.info("Intent classified as tools", message=user_message[:50])
        return "tools"
    
    # FAQ keywords (simple questions)
    faq_keywords = [
        "what is", "who are", "where is", "how much", "price", "cost",
        "hours", "open", "closed", "contact", "phone", "address"
    ]
    if any(keyword in message_lower for keyword in faq_keywords) and len(message_lower.split()) < 15:
        logger.info("Intent classified as FAQ", message=user_message[:50])
        return "faq"
    
    # Default to RAG for complex queries
    logger.info("Intent classified as RAG", message=user_message[:50])
    return "rag"


def classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for intent classification.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with intent classification
    """
    user_message = state.get("user_message", "")
    business_context = state.get("business_context", {})
    
    intent = classify_intent(user_message, business_context)
    
    state["intent"] = intent
    state["next_node"] = intent
    
    logger.info("Intent classification completed", intent=intent)
    
    return state

