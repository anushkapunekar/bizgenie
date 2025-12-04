"""
Chat API (Mode A) – Simple, stable, no LangGraph, no tools.

- Uses RAG node directly
- Creates a Lead on first message
- Sends email/WhatsApp notification if enabled
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Business, Lead
from app.schemas import ChatRequest, ChatResponse
from app.agents.nodes.rag import generate_answer
from app.config import get_settings
from app.tools.email_mcp import send_email
from app.tools.whatsapp_mcp import send_whatsapp_message

router = APIRouter(prefix="/chat", tags=["chat"])
logger = structlog.get_logger(__name__)
settings = get_settings()


def _business_context(b: Business) -> dict:
  return {
      "id": b.id,
      "name": b.name,
      "description": b.description,
      "services": b.services or [],
      "working_hours": b.working_hours or {},
      "contact_email": b.contact_email,
      "contact_phone": b.contact_phone,
  }


async def _notify_new_lead(business: Business, name: str, msg: str) -> None:
  summary = f"New chat lead for {business.name}:\nName: {name}\nMessage: {msg[:200]}"

  # email
  if settings.EMAIL_MCP_ENABLED and business.contact_email:
      try:
          await send_email(
              to=business.contact_email,
              subject=f"New Lead from {name}",
              body=summary,
          )
      except Exception as exc:
          logger.warning("chat.lead_email_failed", error=str(exc))

  # whatsapp (optional; will no-op if disabled)
  if settings.WHATSAPP_MCP_ENABLED and business.contact_phone:
      try:
          await send_whatsapp_message(
              to=business.contact_phone,
              message=summary,
          )
      except Exception as exc:
          logger.warning("chat.lead_whatsapp_failed", error=str(exc))


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
  # 1) Load business
  business = db.query(Business).filter(Business.id == request.business_id).first()
  if not business:
      raise HTTPException(status_code=404, detail="Business not found")

  # 2) Create lead on first message
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
      await _notify_new_lead(business, request.user_name, request.user_message)

  # 3) RAG answer (NO tools, no JSON)
  try:
      context = _business_context(business)
      rag_result = generate_answer(
          business_id=business.id,
          user_message=request.user_message,
          metadata_context=context,
      )
      reply_text = rag_result.get("reply") or (
          "Thanks for your message. I can share our services, hours, "
          "and basic info. Try asking about services or booking."
      )
  except Exception as exc:
      logger.error("chat.rag_failed", error=str(exc))
      reply_text = (
          "I'm having a bit of trouble answering right now, "
          "but you can ask again or contact the business directly."
      )
      rag_result = {"documents_used": 0}

  # 4) Always respond with plain text, no tool actions
  return ChatResponse(
      reply=reply_text,
      conversation_id=request.conversation_id or f"conv_{business.id}",
      tool_actions=[],
      intent=None,
  )
