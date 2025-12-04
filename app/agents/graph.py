from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
from app.agents.nodes.rag import generate_rag_reply

class AgentState(TypedDict, total=False):
    user_message: str
    business_id: int
    business_context: Dict[str, Any]
    response: str
    tool_actions: list

def answer_node(state: AgentState):
    msg = state["user_message"]
    bid = state["business_id"]
    ctx = state.get("business_context", {})

    result = generate_rag_reply(
        business_id=bid,
        user_message=msg,
        metadata_context=ctx
    )

    state["response"] = result["reply"]
    state["tool_actions"] = result.get("tool_actions", [])
    return state

graph = StateGraph(AgentState)
graph.add_node("answer", answer_node)
graph.set_entry_point("answer")
graph.add_edge("answer", END)

agent_graph = graph.compile()

def run_agent(*, business_id: int, user_message: str, business_context: Dict[str, Any]):
    initial = {
        "business_id": business_id,
        "user_message": user_message,
        "business_context": business_context,
    }
    return agent_graph.invoke(initial)
