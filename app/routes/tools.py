"""
Tooling endpoints for WhatsApp, Email, and Calendar MCP actions.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.tools.calendar_mcp import create_event
from app.tools.email_mcp import send_daily_summary, send_email
from app.tools.whatsapp_mcp import send_whatsapp_blast, send_whatsapp_message

router = APIRouter(prefix="/tools", tags=["tools"])
logger = structlog.get_logger(__name__)
settings = get_settings()


def require_api_key(x_api_key: str = Header(...)) -> None:
    if not settings.API_SERVICE_KEY or x_api_key != settings.API_SERVICE_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


class WhatsAppRequest(BaseModel):
    to: str = Field(..., description="E.164 formatted phone number")
    message: str
    type: str = Field(default="text")
    template: Optional[dict] = None


class WhatsAppBlastRequest(BaseModel):
    numbers: List[str]
    message: str


class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str


class DailySummaryRequest(BaseModel):
    to: EmailStr
    summary_text: str


class CalendarEventRequest(BaseModel):
    title: str
    start_dt: datetime
    end_dt: datetime
    description: str
    attendees_emails: List[EmailStr]
    location: Optional[str] = None
    send_via_email: bool = True
    send_via_whatsapp: bool = False


@router.post("/send-whatsapp")
async def post_whatsapp(
    payload: WhatsAppRequest,
    _: None = Depends(require_api_key),
):
    result = await send_whatsapp_message(
        to=payload.to,
        message=payload.message,
        type=payload.type,
        template=payload.template,
    )
    return result


@router.post("/send-blast")
async def post_whatsapp_blast(
    payload: WhatsAppBlastRequest,
    _: None = Depends(require_api_key),
):
    result = await send_whatsapp_blast(payload.numbers, payload.message)
    return result


@router.post("/send-email")
async def post_send_email(
    payload: EmailRequest,
    _: None = Depends(require_api_key),
):
    result = await send_email(payload.to, payload.subject, payload.body)
    return result


@router.post("/send-daily-summary")
async def post_daily_summary(
    payload: DailySummaryRequest,
    _: None = Depends(require_api_key),
):
    result = await send_daily_summary(payload.to, payload.summary_text)
    return result


@router.post("/create-event")
async def post_create_event(
    payload: CalendarEventRequest,
    _: None = Depends(require_api_key),
):
    result = await create_event(
        title=payload.title,
        start_dt=payload.start_dt,
        end_dt=payload.end_dt,
        description=payload.description,
        attendees_emails=[str(email) for email in payload.attendees_emails],
        location=payload.location,
        send_via_email=payload.send_via_email,
        send_via_whatsapp=payload.send_via_whatsapp,
    )
    return result

