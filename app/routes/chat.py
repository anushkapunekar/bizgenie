"""
Chat API: fetch business, run RAG answer, return reply.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.graph import run_agent
from app.database import get_db
from app.models import Business, Lead
from app.schemas import ChatRequest, ChatResponse
from app.config import get_settings
from app.tools.whatsapp_mcp import send_whatsapp_message
from app.tools.email_mcp import send_email

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


async def notify_new_lead(business: Business, lead_name: str, initial_message: str) -> None:
    summary = (
        f"New chat lead for {business.name}:\n"
        f"Name: {lead_name}\n"
        f"Message: {initial_message[:200]}"
    )

    if settings.EMAIL_MCP_ENABLED and business.contact_email:
        try:
            result = await send_email(
                to=business.contact_email,
                subject=f"New Lead from {lead_name}",
                body=summary,
            )
            logger.info("chat.lead_email_notification", result=result)
        except Exception as exc:
            logger.warning("chat.lead_email_failed", error=str(exc))

    if settings.WHATSAPP_MCP_ENABLED and business.contact_phone:
        try:
            result = await send_whatsapp_message(
                to=business.contact_phone,
                message=summary,
            )
            logger.info("chat.lead_whatsapp_notification", result=result)
        except Exception as exc:
            logger.warning("chat.lead_whatsapp_failed", error=str(exc))


def _business_context(biz: Business) -> dict:
    return {
        "id": biz.id,
        "name": biz.name,
        "description": biz.description,
        "services": biz.services or [],
        "working_hours": biz.working_hours or {},
        "contact_email": biz.contact_email,
        "contact_phone": biz.contact_phone,
    }


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    business = db.query(Business).filter(Business.id == request.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Ensure each new conversation creates a lead entry (optional but helpful)
    if not request.conversation_id:
        lead = Lead(
            business_id=business.id,
            name=request.user_name,
            source="chat",
            notes=f"Initial message: {request.user_message[:200]}",
        )
        db.add(lead)
        db.commit()
        logger.info("chat.lead_created", business_id=business.id, lead_id=lead.id)
        await notify_new_lead(business, request.user_name, request.user_message)

    agent_result = run_agent(
        business_id=business.id,
        user_message=request.user_message,
        business_context=_business_context(business),
    )

    logger.info(
        "chat.response_ready",
        business_id=business.id,
        documents_used=agent_result["documents_used"],
    )

    return ChatResponse(
        reply=agent_result["reply"],
        conversation_id=request.conversation_id or f"conv_{business.id}",
        tool_actions=[],
        intent=None,
    )