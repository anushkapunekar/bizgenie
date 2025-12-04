"""
Calendar MCP Tool (Business-side helper)

For now:
- When an appointment is created, we call create_event(...)
- This sends a notification email to the business "calendar owner"
- No user OAuth, no Google API complexity
"""

from __future__ import annotations
import os
from typing import List, Optional
import structlog

from app.tools.email_mcp import send_email

logger = structlog.get_logger(__name__)

CALENDAR_ENABLED = os.getenv("CALENDAR_MCP_ENABLED", "false").lower() == "true"
CALENDAR_SENDER_EMAIL = os.getenv("CALENDAR_SENDER_EMAIL", "")


async def create_event(
    title: str,
    description: Optional[str] = None,
    start_dt: Optional[str] = None,
    end_dt: Optional[str] = None,
    location: Optional[str] = None,
    attendees_emails: Optional[List[str]] = None,
    send_via_email: bool = True,
    send_via_whatsapp: bool = False,  # currently ignored
) -> dict:
    """
    Minimal calendar event helper.

    We treat this as:
    - Construct a nice summary
    - Email it to CALENDAR_SENDER_EMAIL (business owner)
    """
    if not CALENDAR_ENABLED:
        logger.warning("calendar_mcp.disabled")
        return {"status": "disabled"}

    if not CALENDAR_SENDER_EMAIL:
        logger.error("calendar_mcp.no_sender_email")
        return {"status": "error", "detail": "CALENDAR_SENDER_EMAIL not set"}

    body_lines = [
        f"New calendar event created via BizGenie:",
        f"Title: {title}",
    ]
    if description:
        body_lines.append(f"\nDescription: {description}")
    if start_dt:
        body_lines.append(f"\nStart: {start_dt}")
    if end_dt:
        body_lines.append(f"End: {end_dt}")
    if location:
        body_lines.append(f"\nLocation: {location}")
    if attendees_emails:
        body_lines.append(f"\nAttendees: {', '.join(attendees_emails)}")

    body = "\n".join(body_lines)

    try:
        if send_via_email:
            await send_email(
                to=CALENDAR_SENDER_EMAIL,
                subject=f"[BizGenie] Calendar Event: {title}",
                body=body,
            )
        logger.info("calendar_mcp.create_event_sent", title=title)
        return {"status": "ok"}
    except Exception as exc:
        logger.error("calendar_mcp.create_event_failed", error=str(exc))
        return {"status": "error", "detail": str(exc)}


async def update_event(*args, **kwargs) -> dict:
    """Stub for future updates."""
    logger.info("calendar_mcp.update_event_called", args=args, kwargs=kwargs)
    return {"status": "ok", "detail": "update_event stub"}


async def cancel_event(*args, **kwargs) -> dict:
    """Stub for future cancel logic."""
    logger.info("calendar_mcp.cancel_event_called", args=args, kwargs=kwargs)
    return {"status": "ok", "detail": "cancel_event stub"}
