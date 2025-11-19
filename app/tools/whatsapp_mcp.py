"""
WhatsApp MCP tool powered by UltraMsg API.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


def _mask(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    if len(token) <= 6:
        return "*" * len(token)
    return f"{token[:3]}{'*' * (len(token) - 6)}{token[-3:]}"


def _is_enabled() -> bool:
    return bool(settings.WHATSAPP_MCP_ENABLED and settings.ULTRAMSG_TOKEN)


async def _post_whatsapp(form_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    UltraMsg uses form-data, not JSON.
    """
    if not _is_enabled():
        return {
            "success": False,
            "message": "WhatsApp MCP disabled or misconfigured",
            "details": {"enabled": settings.WHATSAPP_MCP_ENABLED},
        }

    instance_id = settings.ULTRAMSG_INSTANCE_ID
    token = settings.ULTRAMSG_TOKEN
    api_base = settings.ULTRAMSG_API_BASE or "https://api.ultramsg.com"

    if not instance_id or not token:
        return {
            "success": False,
            "message": "UltraMsg credentials missing",
            "details": {"instance_id": instance_id, "token": bool(token)},
        }

    url = f"{api_base}/{instance_id}/messages"

    logger.info(
        "whatsapp.request",
        url=url,
        payload=form_payload,
        token=_mask(token),
    )

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.post(url, data=form_payload)
        except httpx.HTTPError as exc:
            logger.error("whatsapp.http_error", error=str(exc))
            return {
                "success": False,
                "message": "HTTP error sending WhatsApp message",
                "details": {"error": str(exc)},
            }

    if response.status_code >= 400:
        logger.error(
            "whatsapp.http_failure",
            status=response.status_code,
            body=response.text,
        )
        return {
            "success": False,
            "message": "UltraMsg API error",
            "details": {
                "status": response.status_code,
                "body": response.text,
            },
        }

    data = response.json()
    logger.info("whatsapp.http_success", response=data)
    return {
        "success": True,
        "message": "WhatsApp message sent",
        "details": data,
    }


def _format_body(message: str) -> str:
    sender = settings.WHATSAPP_SENDER_NAME or "BizGenie"
    footer = "\n\nReply STOP to unsubscribe."
    return f"{sender}:\n{message.strip()}{footer}"


async def send_whatsapp_message(
    to: str,
    message: str,
    type: str = "text",
    template: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    UltraMsg does NOT support WhatsApp templates.
    We fallback to text messages always.
    """
    formatted = _format_body(message)

    payload = {
        "token": settings.ULTRAMSG_TOKEN,
        "to": to,
        "body": formatted,
    }

    return await _post_whatsapp(payload)


async def send_whatsapp_blast(numbers: List[str], message: str) -> Dict[str, Any]:
    """Send a campaign blast to multiple numbers."""
    results = []
    for number in numbers:
        result = await send_whatsapp_message(number, message)
        results.append({"number": number, "result": result})

    success_count = sum(1 for r in results if r["result"]["success"])
    logger.info(
        "whatsapp.blast_summary",
        requested=len(numbers),
        succeeded=success_count,
    )

    return {
        "success": success_count == len(numbers),
        "message": f"Sent WhatsApp blast to {success_count}/{len(numbers)} recipients",
        "details": results,
    }


async def test_whatsapp() -> Dict[str, Any]:
    """Validate UltraMsg configuration without sending a message."""
    details = {
        "enabled": settings.WHATSAPP_MCP_ENABLED,
        "instance_id": settings.ULTRAMSG_INSTANCE_ID,
        "token_present": bool(settings.ULTRAMSG_TOKEN),
        "api_base": settings.ULTRAMSG_API_BASE,
        "sender_name": settings.WHATSAPP_SENDER_NAME,
    }

    ok = all(
        [
            settings.WHATSAPP_MCP_ENABLED,
            settings.ULTRAMSG_INSTANCE_ID,
            settings.ULTRAMSG_TOKEN,
        ]
    )

    message = (
        "UltraMsg WhatsApp MCP configuration valid"
        if ok else
        "UltraMsg WhatsApp MCP configuration incomplete"
    )

    logger.info("whatsapp.test", **details)
    return {
        "success": ok,
        "message": message,
        "details": details,
    }
