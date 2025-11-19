"""
Calendar MCP utilities: create events, generate ICS, send notifications.
Updated with lightweight update_event and cancel_event wrappers.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from email.utils import formatdate
from typing import Any, Dict, List, Optional

import structlog

from app.config import get_settings
from app.tools.email_mcp import send_email
from app.tools.whatsapp_mcp import send_whatsapp_message

logger = structlog.get_logger(__name__)
settings = get_settings()


def generate_ics_event(
    *,
    title: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    """Return ICS file content as string."""
    uid = f"{uuid.uuid4()}@bizgenie"

    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BizGenie//Calendar MCP//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{fmt(start_dt)}",
        f"DTSTART:{fmt(start_dt)}",
        f"DTEND:{fmt(end_dt)}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{description}",
    ]
    if location:
        lines.append(f"LOCATION:{location}")
    for attendee in attendees or []:
        lines.append(f"ATTENDEE;RSVP=TRUE:mailto:{attendee}")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    return "\n".join(lines)


async def create_event(
    title: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str,
    attendees_emails: List[str],
    location: Optional[str] = None,
    send_via_email: bool = True,
    send_via_whatsapp: bool = False,
) -> Dict[str, Any]:
    """Create an event and optionally send via email/WhatsApp."""
    if not settings.CALENDAR_MCP_ENABLED:
        return {
            "success": False,
            "message": "Calendar MCP disabled",
            "details": {},
        }

    ics_content = generate_ics_event(
        title=title,
        start_dt=start_dt,
        end_dt=end_dt,
        description=description,
        location=location,
        attendees=attendees_emails,
    )

    details: Dict[str, Any] = {
        "title": title,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "attendees": attendees_emails,
        "location": location,
    }

    if send_via_email and attendees_emails:
        attachments = [
            {
                "filename": f"{title}.ics",
                "mime_type": "text/calendar",
                "content": ics_content.encode("utf-8"),
            }
        ]
        email_body = (
            f"You have a new event:\n\n{title}\n"
            f"Start: {start_dt}\nEnd: {end_dt}\n\n{description}"
        )
        for attendee in attendees_emails:
            result = await send_email(
                to=attendee,
                subject=f"New Event: {title}",
                body=email_body,
                attachments=attachments,
            )
            details.setdefault("emails_sent", []).append({"to": attendee, "result": result})

    if send_via_whatsapp:
        message = (
            f"Event Confirmation:\n{title}\nStart: {start_dt}\nEnd: {end_dt}\n"
            f"{description}\nLocation: {location or 'TBD'}"
        )
        logger.info("calendar.whatsapp_sent", message_preview=message[:160])

    return {"success": True, "message": "Event created", "details": details}


# --------------------------------------------------------
# NEW: Lightweight UPDATE EVENT
# --------------------------------------------------------
async def update_event(
    *,
    title: str,
    new_start: datetime,
    new_end: datetime,
    description: str,
    attendees_emails: List[str],
    location: Optional[str] = None,
    send_via_email: bool = True,
    send_via_whatsapp: bool = False,
) -> Dict[str, Any]:
    """Send updated event details to attendees (lightweight wrapper)."""

    details = {
        "title": title,
        "new_start": new_start.isoformat(),
        "new_end": new_end.isoformat(),
        "attendees": attendees_emails,
        "location": location,
    }

    # Email update
    if send_via_email and attendees_emails:
        email_body = (
            f"Your event '{title}' has been updated.\n\n"
            f"New Start: {new_start}\nNew End: {new_end}\n\n{description}"
        )
        for attendee in attendees_emails:
            result = await send_email(
                to=attendee,
                subject=f"Updated Event: {title}",
                body=email_body,
            )
            details.setdefault("emails_sent", []).append({"to": attendee, "result": result})

    # WhatsApp update
    if send_via_whatsapp:
        message = (
            f"Event Updated:\n{title}\nNew Start: {new_start}\nNew End: {new_end}\n"
            f"{description}\nLocation: {location or 'TBD'}"
        )
        logger.info("calendar.whatsapp_update", message_preview=message[:160])

    return {"success": True, "message": "Event updated", "details": details}


# --------------------------------------------------------
# NEW: Lightweight CANCEL EVENT
# --------------------------------------------------------
async def cancel_event(
    *,
    title: str,
    attendees_emails: List[str],
    send_via_email: bool = True,
    send_via_whatsapp: bool = False,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Notify attendees that the event is cancelled."""

    details = {
        "title": title,
        "reason": reason or "No longer available",
        "attendees": attendees_emails,
    }

    # Email cancellation
    if send_via_email and attendees_emails:
        email_body = (
            f"Your event '{title}' has been cancelled.\n\n"
            f"Reason: {reason or 'No longer available'}"
        )
        for attendee in attendees_emails:
            result = await send_email(
                to=attendee,
                subject=f"Event Cancelled: {title}",
                body=email_body,
            )
            details.setdefault("emails_sent", []).append({"to": attendee, "result": result})

    # WhatsApp cancellation
    if send_via_whatsapp:
        message = (
            f"Event Cancelled:\n{title}\nReason: {reason or 'No longer available'}"
        )
        logger.info("calendar.whatsapp_cancel", message_preview=message[:160])

    return {"success": True, "message": "Event cancelled", "details": details}


async def test_calendar() -> Dict[str, Any]:
    """Verify calendar settings."""
    details = {
        "enabled": settings.CALENDAR_MCP_ENABLED,
        "sender": settings.CALENDAR_SENDER_EMAIL,
    }
    ok = bool(settings.CALENDAR_MCP_ENABLED and settings.CALENDAR_SENDER_EMAIL)
    msg = "Calendar MCP ready" if ok else "Calendar MCP configuration incomplete"
    logger.info("calendar.test", **details)

    return {
        "success": ok,
        "message": msg,
        "details": details,
    }
