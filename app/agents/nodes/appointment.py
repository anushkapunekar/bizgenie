"""
Appointment scheduling node for the LangGraph agent.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import structlog
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Appointment, Business
from app.tools.calendar_mcp import get_available_slots, generate_appointment_confirmation

logger = structlog.get_logger(__name__)


def extract_appointment_info(user_message: str) -> Dict[str, Any]:
    """
    Extract appointment information from user message.
    
    Args:
        user_message: User's message
    
    Returns:
        Extracted appointment info (date, time, service, etc.)
    """
    # TODO: Use NLP/LLM to extract structured information
    # For now, return placeholder
    return {
        "date": None,
        "time": None,
        "service": None
    }


def appointment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for appointment handling.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with appointment information
    """
    user_message = state.get("user_message", "")
    business_id = state.get("business_id")
    user_name = state.get("user_name", "Customer")
    
    if not business_id:
        state["response"] = "Business context is missing. Please try again."
        state["next_node"] = "end"
        return state
    
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Get business
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            state["response"] = "Business not found."
            state["next_node"] = "end"
            return state
        
        # Extract appointment info (simplified)
        appointment_info = extract_appointment_info(user_message)
        
        # Get available slots for today and tomorrow
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        slots_today = get_available_slots(business_id, today.strftime("%Y-%m-%d"), db=db)
        slots_tomorrow = get_available_slots(business_id, tomorrow.strftime("%Y-%m-%d"), db=db)
        
        if not slots_today and not slots_tomorrow:
            state["response"] = f"I'm sorry, but we don't have any available slots for the next two days. Please contact us directly at {business.contact_phone or business.contact_email or 'our office'} to schedule an appointment."
            state["next_node"] = "end"
            return state
        
        # Format response with available slots
        response_parts = [f"Here are available appointment slots for {business.name}:"]
        
        if slots_today:
            response_parts.append(f"\nToday ({today.strftime('%B %d')}):")
            for slot in slots_today[:5]:  # Show first 5 slots
                response_parts.append(f"  - {slot['time']}")
        
        if slots_tomorrow:
            response_parts.append(f"\nTomorrow ({tomorrow.strftime('%B %d')}):")
            for slot in slots_tomorrow[:5]:
                response_parts.append(f"  - {slot['time']}")
        
        response_parts.append("\nWould you like to book one of these slots? Please let me know your preferred date and time.")
        
        state["response"] = "\n".join(response_parts)
        state["next_node"] = "end"
        state["available_slots"] = {
            "today": slots_today,
            "tomorrow": slots_tomorrow
        }
        
        logger.info("Appointment slots retrieved", business_id=business_id, slots_count=len(slots_today) + len(slots_tomorrow))
        
    except Exception as e:
        logger.error("Error in appointment node", business_id=business_id, error=str(e))
        state["response"] = "I encountered an error while checking availability. Please try again or contact us directly."
        state["next_node"] = "end"
    
    return state

