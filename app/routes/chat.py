"""
Chat API: safe async wrapper for agent. Never crashes.
"""
from __future__ import annotations

import asyncio
from functools import partial

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

router = APIRouter(prefix="/chat", tags=["chat"])
logger = structlog.get_logger(__name__)
settings = get_settings()


async def notify_new_lead(business: Business, name: str, message: str):
    summary = f"New chat lead for {business.name}:\nName: {name}\nMessage: {message[:200]}"

    # Email
    if settings.EMAIL_MCP_ENABLED and business.contact_email:
        try:
            await send_email(
                to=business.contact_email,
                subject=f"New Lead from {name}",
                body=summary
            )
        except Exception:
            pass

    # WhatsApp
    if settings.WHATSAPP_MCP_ENABLED and business.contact_phone:
        try:
            await send_whatsapp_message(
                to=business.contact_phone,
                message=summary
            )
        except Exception:
            pass


def _ctx(b: Business):
    return {
        "id": b.id,
        "name": b.name,
        "description": b.description,
        "services": b.services or [],
        "working_hours": b.working_hours or {},
        "contact_email": b.contact_email,
        "contact_phone": b.contact_phone,
    }


async def _run_agent_async(bid: int, msg: str, ctx: dict):
    loop = asyncio.get_event_loop()
    fn = partial(run_agent, business_id=bid, user_message=msg, business_context=ctx)
    return await loop.run_in_executor(None, fn)


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):

    business = db.query(Business).filter(Business.id == request.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Create lead on NEW conversation
    if not request.conversation_id:
        lead = Lead(
            business_id=business.id,
            name=request.user_name,
            source="chat",
            notes=f"Initial message: {request.user_message[:200]}"
        )
        db.add(lead)
        db.commit()
        await notify_new_lead(business, request.user_name, request.user_message)

    # ----------------------------
    # SAFE AGENT EXECUTION
    # ----------------------------
    try:
        agent_result = await _run_agent_async(
            business.id,
            request.user_message,
            _ctx(business)
        )
    except Exception as exc:
        logger.error("agent.crash", error=str(exc))
        agent_result = {}

    # Extract final reply
    final_reply = (
        agent_result.get("response")
        or agent_result.get("reply")
        or "I’m here but having trouble answering. Try rephrasing?"
    )

    return ChatResponse(
        reply=final_reply,
        conversation_id=request.conversation_id or f"conv_{business.id}",
        tool_actions=agent_result.get("tool_actions", []),
        intent=None,
    )
