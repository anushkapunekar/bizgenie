"""
Chat API routes for interacting with the BizGenie agent.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog
from app.database import get_db
from app.models import Business, Lead
from app.schemas import ChatRequest, ChatResponse
from app.agents.graph import run_agent

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint for interacting with the BizGenie agent.
    
    Args:
        request: Chat request with business_id, user_name, and user_message
        db: Database session
    
    Returns:
        Chat response with reply and tool actions
    """
    try:
        # Get business
        business = db.query(Business).filter(Business.id == request.business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Prepare business context
        business_context = {
            "id": business.id,
            "name": business.name,
            "description": business.description,
            "services": business.services or [],
            "working_hours": business.working_hours or {},
            "contact_email": business.contact_email,
            "contact_phone": business.contact_phone
        }
        
        # Run agent
        result = run_agent(
            user_message=request.user_message,
            user_name=request.user_name,
            business_id=request.business_id,
            business_context=business_context,
            conversation_id=request.conversation_id or ""
        )
        
        # Create lead if this is a new conversation
        if not request.conversation_id:
            try:
                lead = Lead(
                    business_id=request.business_id,
                    name=request.user_name,
                    source="chat",
                    notes=f"Initial message: {request.user_message[:200]}"
                )
                db.add(lead)
                db.commit()
                logger.info("Lead created", business_id=request.business_id, lead_id=lead.id)
            except Exception as e:
                logger.warning("Failed to create lead", error=str(e))
                db.rollback()
        
        logger.info(
            "Chat request processed",
            business_id=request.business_id,
            user_name=request.user_name,
            intent=result.get("intent")
        )
        
        return ChatResponse(
            reply=result["reply"],
            tool_actions=result["tool_actions"],
            conversation_id=result["conversation_id"],
            intent=result.get("intent")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing chat request", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

