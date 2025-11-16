"""
Tools executor node for running MCP tools.
"""
from typing import Dict, Any, List
import structlog
from app.tools.whatsapp_mcp import send_whatsapp_message
from app.tools.email_mcp import send_email
from app.tools.calendar_mcp import generate_appointment_confirmation

logger = structlog.get_logger(__name__)


def extract_tool_requirements(user_message: str) -> Dict[str, Any]:
    """
    Extract tool requirements from user message.
    
    Args:
        user_message: User's message
    
    Returns:
        Dict with tool requirements (tool_type, recipient, content, etc.)
    """
    message_lower = user_message.lower()
    
    # TODO: Use LLM to extract structured information
    # For now, simple keyword-based extraction
    
    requirements = {
        "tool_type": None,
        "recipient": None,
        "content": None
    }
    
    if "whatsapp" in message_lower or "message" in message_lower:
        requirements["tool_type"] = "whatsapp"
    elif "email" in message_lower:
        requirements["tool_type"] = "email"
    elif "appointment" in message_lower and "confirm" in message_lower:
        requirements["tool_type"] = "appointment_confirmation"
    
    return requirements


def tools_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for executing MCP tools.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with tool execution results
    """
    user_message = state.get("user_message", "")
    business_context = state.get("business_context", {})
    tool_actions = state.get("tool_actions", [])
    
    try:
        requirements = extract_tool_requirements(user_message)
        tool_type = requirements.get("tool_type")
        
        if not tool_type:
            state["response"] = "I understand you want me to send a message, but I need more details. Please specify whether you want to send an email or WhatsApp message, and provide the recipient and message content."
            state["next_node"] = "end"
            return state
        
        result = None
        
        if tool_type == "whatsapp":
            # TODO: Extract recipient and message from user_message or state
            recipient = requirements.get("recipient") or business_context.get("contact_phone", "")
            message = requirements.get("content") or user_message
            
            if not recipient:
                state["response"] = "I need a phone number to send a WhatsApp message. Please provide the recipient's phone number."
                state["next_node"] = "end"
                return state
            
            result = send_whatsapp_message(recipient, message)
            tool_actions.append({
                "tool": "whatsapp",
                "action": "send_message",
                "result": result
            })
            
        elif tool_type == "email":
            # TODO: Extract recipient, subject, and body from user_message or state
            recipient = requirements.get("recipient") or business_context.get("contact_email", "")
            subject = f"Message from {business_context.get('name', 'BizGenie')}"
            body = requirements.get("content") or user_message
            
            if not recipient:
                state["response"] = "I need an email address to send an email. Please provide the recipient's email address."
                state["next_node"] = "end"
                return state
            
            result = send_email(recipient, subject, body)
            tool_actions.append({
                "tool": "email",
                "action": "send_email",
                "result": result
            })
            
        elif tool_type == "appointment_confirmation":
            # TODO: Extract appointment_id from state or user_message
            appointment_id = state.get("appointment_id")
            if appointment_id:
                result = generate_appointment_confirmation(appointment_id)
                tool_actions.append({
                    "tool": "calendar",
                    "action": "generate_confirmation",
                    "result": result
                })
        
        if result and result.get("success"):
            state["response"] = f"Action completed successfully. {tool_type} has been sent/processed."
        else:
            error_msg = result.get("error", "Unknown error") if result else "Tool execution failed"
            state["response"] = f"I encountered an issue: {error_msg}. Please try again or contact support."
        
        state["tool_actions"] = tool_actions
        state["next_node"] = "end"
        
        logger.info("Tool executed", tool_type=tool_type, success=result.get("success") if result else False)
        
    except Exception as e:
        logger.error("Error in tools executor node", error=str(e))
        state["response"] = "I encountered an error while executing the requested action. Please try again."
        state["next_node"] = "end"
    
    return state

