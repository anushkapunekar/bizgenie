"""
RAG node for answering questions using document retrieval.
"""
from typing import Dict, Any, List
import structlog
from app.rag.vectorstore import vector_store
from app.llm_service import llm_service

logger = structlog.get_logger(__name__)


def rag_query(user_message: str, business_id: int, n_results: int = 3) -> str:
    """
    Query RAG system and generate answer.
    
    Args:
        user_message: User's question
        business_id: Business identifier
        n_results: Number of documents to retrieve
    
    Returns:
        Generated answer based on retrieved documents
    """
    try:
        # Query vector store
        relevant_docs = vector_store.query_documents(
            business_id=business_id,
            query=user_message,
            n_results=n_results
        )
        
        if not relevant_docs:
            logger.warning("No relevant documents found", business_id=business_id)
            return "I couldn't find specific information about that in our documents. Could you please rephrase your question or contact us directly?"
        
        # Build context from retrieved documents
        context = "\n\n".join([doc["text"] for doc in relevant_docs[:3]])
        
        # Use free LLM to generate answer from retrieved documents
        answer = llm_service.generate(
            prompt=user_message,
            context=context
        )
        
        logger.info(
            "RAG query completed",
            business_id=business_id,
            docs_retrieved=len(relevant_docs)
        )
        
        return answer
    except Exception as e:
        logger.error("Error in RAG query", business_id=business_id, error=str(e))
        return "I encountered an error while searching our documents. Please try again or contact us directly."


def rag_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for RAG-based answering.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with RAG answer
    """
    user_message = state.get("user_message", "")
    business_id = state.get("business_id")
    
    if not business_id:
        state["response"] = "Business context is missing. Please try again."
        state["next_node"] = "end"
        return state
    
    answer = rag_query(user_message, business_id)
    
    state["response"] = answer
    state["next_node"] = "end"
    
    logger.info("RAG node completed", business_id=business_id)
    
    return state

