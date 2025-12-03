"""
WhatsApp MCP Tool (UltraMsg Version)
Supports:
- send_whatsapp_message
- confirmation
- update
- cancellation
- followup
"""

import os
import aiohttp
import structlog
import json
from typing import Optional

logger = structlog.get_logger(__name__)

ULTRA_INSTANCE = os.getenv("ULTRAMSG_INSTANCE_ID", "")
ULTRA_TOKEN = os.getenv("ULTRAMSG_TOKEN", "")
ULTRA_BASE = os.getenv("ULTRAMSG_API_BASE", "").rstrip("/")

WHATSAPP_ENABLED = os.getenv("WHATSAPP_MCP_ENABLED", "false").lower() == "true"


async def _ultramsg_send(to: str, message: str) -> dict:
    """UltraMsg message sender."""
    if not WHATSAPP_ENABLED:
        logger.warning("WhatsApp MCP disabled")
        return {"status": "disabled"}

    if not ULTRA_INSTANCE or not ULTRA_TOKEN or not ULTRA_BASE:
        logger.error("UltraMsg not configured")
        return {"status": "error", "detail": "Misconfigured UltraMsg API"}

    sender_number = os.getenv("ULTRAMSG_PHONE", "")
    if not sender_number:
        logger.error("ULTRAMSG_PHONE missing in .env")
        return {"status": "error", "detail": "Missing sender WhatsApp number"}

    url = f"{ULTRA_BASE}/messages/chat"

    payload = {
        "token": ULTRA_TOKEN,
        "to": to,
        "from": sender_number,  # required by UltraMsg
        "body": message,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                text = await resp.text()

        logger.warning("ultramsg.debug_raw_response", raw=text)

        try:
            data = json.loads(text)
        except:
            logger.error("ultramsg.invalid_json", payload=text)
            return {"status": "error", "detail": "Invalid JSON from UltraMsg", "raw": text}

        logger.info("ultramsg.sent", response=data)
        return data

    except Exception as e:
        logger.error("ultramsg.error", error=str(e))
        return {"status": "error", "detail": str(e)}


# ----------------------------------------------------------
# HIGH LEVEL TOOL FUNCTIONS (Used by LangGraph tool router)
# ----------------------------------------------------------

async def send_whatsapp_message(to: str, message: str):
    return await _ultramsg_send(to, message)


async def send_whatsapp_confirmation(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been confirmed. Thank you!"
    return await _ultramsg_send(to, msg)


async def send_whatsapp_update(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been updated."
    return await _ultramsg_send(to, msg)


async def send_whatsapp_cancellation(to: str, message: Optional[str] = None):
    msg = message or "Your appointment has been cancelled."
    return await _ultramsg_send(to, msg)


async def send_whatsapp_followup(to: str, message: Optional[str] = None):
    msg = message or "Hope your experience was great! Let us know if you need anything else."
    return await _ultramsg_send(to, msg)
