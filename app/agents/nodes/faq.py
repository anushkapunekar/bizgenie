"""
FAQ node for answering simple frequently asked questions.
"""
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


def answer_faq(user_message: str, business_context: Dict[str, Any]) -> str:
    """
    Answer simple FAQ questions based on business context.
    
    Args:
        user_message: User's question
        business_context: Business information
    
    Returns:
        Answer to the FAQ
    """
    message_lower = user_message.lower()
    business_name = business_context.get("name", "we")
    services = business_context.get("services", [])
    working_hours = business_context.get("working_hours", {})
    contact_email = business_context.get("contact_email", "")
    contact_phone = business_context.get("contact_phone", "")
    
    # Handle different FAQ types
    if "what is" in message_lower or "who are" in message_lower:
        description = business_context.get("description", f"{business_name} is a business.")
        return f"{business_name} is {description}"
    
    if "services" in message_lower or "what do" in message_lower:
        if services:
            services_list = ", ".join(services)
            return f"{business_name} offers the following services: {services_list}."
        return f"Please contact {business_name} for information about our services."
    
    if "hours" in message_lower or "open" in message_lower or "closed" in message_lower:
        if working_hours:
            hours_text = []
            for day, times in working_hours.items():
                if times:
                    hours_text.append(f"{day.capitalize()}: {times.get('open', 'N/A')} - {times.get('close', 'N/A')}")
            return f"{business_name} is open:\n" + "\n".join(hours_text)
        return f"Please contact {business_name} for our business hours."
    
    if "contact" in message_lower or "phone" in message_lower or "email" in message_lower:
        contact_info = []
        if contact_phone:
            contact_info.append(f"Phone: {contact_phone}")
        if contact_email:
            contact_info.append(f"Email: {contact_email}")
        if contact_info:
            return f"You can reach {business_name} at:\n" + "\n".join(contact_info)
        return f"Please check our website for contact information."
    
    # Default response
    return f"I'm here to help with information about {business_name}. How can I assist you?"


def faq_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for FAQ handling.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with FAQ answer
    """
    user_message = state.get("user_message", "")
    business_context = state.get("business_context", {})
    
    answer = answer_faq(user_message, business_context)
    
    state["response"] = answer
    state["next_node"] = "end"
    
    logger.info("FAQ answered", question_length=len(user_message))
    
    return state

