"""
Calendar MCP Tool — Final Working Version
Handles:
- create_event
- update_event
- cancel_event
Synchronizes DB + emails + WhatsApp
"""

import os
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Appointment, Business
from app.tools.email_mcp import send_email
from app.tools.whatsapp_mcp import send_whatsapp_message

logger = structlog.get_logger(__name__)

CALENDAR_ENABLED = os.getenv("CALENDAR_MCP_ENABLED", "false").lower() == "true"


def _get_db():
    return SessionLocal()


def _parse_dt(date: Optional[str], time: Optional[str]) -> Optional[datetime]:
    if not date or not time:
        return None
    try:
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except:
        return None


# ----------------------------------------------------------------
# CREATE EVENT
# ----------------------------------------------------------------
async def create_event(
    title: str,
    date: Optional[str] = None,
    time: Optional[str] = None,
    description: Optional[str] = None,
    business_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    send_via_email: bool = True,
    send_via_whatsapp: bool = True,
    **kwargs
):
    if not CALENDAR_ENABLED:
        logger.warning("Calendar MCP disabled")
        return {"status": "disabled"}

    db = _get_db()

    business = None
    if business_id:
        business = db.query(Business).filter(Business.id == business_id).first()

    start_dt = _parse_dt(date, time)
    if not start_dt:
        logger.error("Invalid datetime for create_event")
        return {"status": "error", "detail": "Invalid date/time"}

    end_dt = start_dt + timedelta(minutes=45)

    # store in DB
    appt = Appointment(
        business_id=business_id,
        customer_name=customer_name or "Guest",
        customer_email=customer_email,
        start_datetime=start_dt,
        end_datetime=end_dt,
        notes=description,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # send email
    if send_via_email and business:
        try:
            await send_email(
                to=customer_email,
                subject="Your Appointment is Confirmed",
                body=f"Your appointment at {business.name} is booked for {start_dt}."
            )
        except Exception as e:
            logger.error("calendar.email_failed", error=str(e))

    # send WhatsApp
    if send_via_whatsapp and business and business.contact_phone:
        try:
            await send_whatsapp_message(
                to=business.contact_phone,
                message=f"New Appointment:\n{appt.customer_name}\n{start_dt}"
            )
        except Exception as e:
            logger.error("calendar.whatsapp_failed", error=str(e))

    logger.info("calendar.created", appt_id=appt.id)

    return {
        "status": "success",
        "event_id": appt.id,
        "start": str(start_dt),
        "end": str(end_dt),
    }


# ----------------------------------------------------------------
# UPDATE EVENT
# ----------------------------------------------------------------
async def update_event(event_id: int, date: str = None, time: str = None, **kwargs):
    if not CALENDAR_ENABLED:
        return {"status": "disabled"}
    db = _get_db()

    appt = db.query(Appointment).filter(Appointment.id == event_id).first()
    if not appt:
        return {"status": "error", "detail": "Appointment not found"}

    new_start = _parse_dt(date, time)
    if not new_start:
        return {"status": "error", "detail": "Invalid date/time"}

    appt.start_datetime = new_start
    appt.end_datetime = new_start + timedelta(minutes=45)
    db.commit()

    logger.info("calendar.updated", appt_id=appt.id)
    return {"status": "updated", "event_id": appt.id}


# ----------------------------------------------------------------
# CANCEL EVENT
# ----------------------------------------------------------------
async def cancel_event(event_id: int, **kwargs):
    if not CALENDAR_ENABLED:
        return {"status": "disabled"}
    db = _get_db()

    appt = db.query(Appointment).filter(Appointment.id == event_id).first()
    if not appt:
        return {"status": "error", "detail": "Appointment not found"}

    db.delete(appt)
    db.commit()

    logger.info("calendar.cancelled", event_id=event_id)
    return {"status": "cancelled", "event_id": event_id}
