"""
WhatsApp MCP Tool – SAFE STUB VERSION

- Does NOT call any external API (UltraMsg etc.)
- Never crashes the app
- Just logs what *would* be sent
"""

import os
import structlog
from typing import Optional, Dict, Any

logger = structlog.get_logger(__name__)

WHATSAPP_ENABLED = os.getenv("WHATSAPP_MCP_ENABLED", "false").lower() == "true"
WHATSAPP_SENDER_NAME = os.getenv("WHATSAPP_SENDER_NAME", "BizGenie")


async def _log_whatsapp(to: str, message: str) -> Dict[str, Any]:
    """
    Safe internal stub – mimic sending WhatsApp and log it.
    """
    if not WHATSAPP_ENABLED:
        logger.info(
            "whatsapp.disabled",
            to=to,
            message=message[:200],
        )
        return {"status": "disabled"}

    logger.info(
        "whatsapp.sent_stub",
        to=to,
        sender=WHATSAPP_SENDER_NAME,
        preview=message[:200],
    )
    return {"status": "ok", "to": to}


async def send_whatsapp_message(to: str, message: str):
    return await _log_whatsapp(to, message)


async def send_whatsapp_confirmation(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been confirmed. Thank you!"
    return await _log_whatsapp(to, msg)


async def send_whatsapp_update(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been updated."
    return await _log_whatsapp(to, msg)


async def send_whatsapp_cancellation(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been cancelled."
    return await _log_whatsapp(to, msg)


async def send_whatsapp_followup(to: str, message: Optional[str] = None):
    msg = message or "Hope your experience was great! Let us know if you need anything else."
    return await _log_whatsapp(to, msg)
