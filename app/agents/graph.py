"""
LangGraph agent graph for BizGenie.
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
import structlog
from app.agents.nodes.classify import classify_node
from app.agents.nodes.faq import faq_node
from app.agents.nodes.rag import rag_node
from app.agents.nodes.appointment import appointment_node
from app.agents.nodes.tools_executor import tools_executor_node

logger = structlog.get_logger(__name__)


class AgentState:
    """State definition for the LangGraph agent."""
    user_message: str
    user_name: str
    business_id: int
    business_context: Dict[str, Any]
    intent: Literal["faq", "rag", "appointment", "tools", None] = None
    next_node: str = "classify"
    response: str = ""
    tool_actions: list = []
    conversation_id: str = ""


def route_to_node(state: Dict[str, Any]) -> str:
    """
    Route to the next node based on intent.
    
    Args:
        state: Current agent state
    
    Returns:
        Next node name
    """
    next_node = state.get("next_node", "end")
    logger.debug("Routing to node", next_node=next_node)
    return next_node


def create_agent_graph() -> StateGraph:
    """
    Create and configure the LangGraph agent.
    
    Returns:
        Configured StateGraph
    """
    # Create graph
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("appointment", appointment_node)
    workflow.add_node("tools_executor", tools_executor_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add conditional edges from classify
    workflow.add_conditional_edges(
        "classify",
        route_to_node,
        {
            "faq": "faq",
            "rag": "rag",
            "appointment": "appointment",
            "tools": "tools_executor",
            "end": END
        }
    )
    
    # All other nodes go to END
    workflow.add_edge("faq", END)
    workflow.add_edge("rag", END)
    workflow.add_edge("appointment", END)
    workflow.add_edge("tools_executor", END)
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("Agent graph created and compiled")
    
    return app


# Global agent instance
agent_graph = create_agent_graph()


def run_agent(
    user_message: str,
    user_name: str,
    business_id: int,
    business_context: Dict[str, Any],
    conversation_id: str = ""
) -> Dict[str, Any]:
    """
    Run the agent with given inputs.
    
    Args:
        user_message: User's message
        user_name: User's name
        business_id: Business identifier
        business_context: Business information
        conversation_id: Optional conversation ID for context
    
    Returns:
        Agent response with reply and tool actions
    """
    try:
        # Initialize state
        initial_state = {
            "user_message": user_message,
            "user_name": user_name,
            "business_id": business_id,
            "business_context": business_context,
            "intent": None,
            "next_node": "classify",
            "response": "",
            "tool_actions": [],
            "conversation_id": conversation_id or f"conv_{business_id}_{hash(user_message)}"
        }
        
        # Run agent
        final_state = agent_graph.invoke(initial_state)
        
        logger.info(
            "Agent execution completed",
            business_id=business_id,
            intent=final_state.get("intent"),
            has_response=bool(final_state.get("response"))
        )
        
        return {
            "reply": final_state.get("response", "I'm sorry, I couldn't generate a response. Please try again."),
            "tool_actions": final_state.get("tool_actions", []),
            "conversation_id": final_state.get("conversation_id", ""),
            "intent": final_state.get("intent")
        }
    except Exception as e:
        logger.error("Error running agent", business_id=business_id, error=str(e))
        return {
            "reply": "I encountered an error while processing your request. Please try again.",
            "tool_actions": [],
            "conversation_id": conversation_id or "",
            "intent": None
        }

