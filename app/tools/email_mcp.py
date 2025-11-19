"""
Email MCP tools using async SMTP (aiosmtplib).
"""
from __future__ import annotations

import asyncio
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiosmtplib
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


def _mask(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def _is_valid_email(address: str) -> bool:
    name, email = parseaddr(address)
    return bool(email and "@" in email and "." in email.split("@")[-1])


def _is_enabled() -> bool:
    return bool(settings.EMAIL_MCP_ENABLED and settings.EMAIL_HOST and settings.EMAIL_USERNAME)


def _build_message(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[Dict[str, Union[str, bytes, Path]]]] = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = settings.EMAIL_USERNAME or "noreply@bizgenie.ai"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    for attachment in attachments or []:
        filename = attachment.get("filename")
        mime = attachment.get("mime_type", "application/octet-stream")
        content = attachment.get("content")
        maintype, subtype = mime.split("/", 1)

        if isinstance(content, Path):
            data = content.read_bytes()
        elif isinstance(content, bytes):
            data = content
        elif isinstance(content, str):
            data = Path(content).read_bytes()
        else:
            raise ValueError("Unsupported attachment content type")

        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    return msg


async def _send_message(msg: EmailMessage) -> Dict[str, Any]:
    if not _is_enabled():
        return {
            "success": False,
            "message": "Email MCP disabled or misconfigured",
            "details": {"enabled": settings.EMAIL_MCP_ENABLED},
        }

    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT or 587
    username = settings.EMAIL_USERNAME
    password = settings.EMAIL_PASSWORD

    logger.info(
        "email.smtp_connect",
        host=host,
        port=port,
        username=username,
        password=_mask(password),
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=host,
            port=port,
            username=username,
            password=password,
            start_tls=True,
        )
    except aiosmtplib.SMTPException as exc:
        logger.error("email.smtp_error", error=str(exc))
        return {
            "success": False,
            "message": "SMTP error sending email",
            "details": {"error": str(exc)},
        }

    logger.info("email.sent", to=msg["To"], subject=msg["Subject"])
    return {
        "success": True,
        "message": "Email sent successfully",
        "details": {"to": msg["To"], "subject": msg["Subject"]},
    }


async def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[Dict[str, Union[str, bytes, Path]]]] = None,
) -> Dict[str, Any]:

    if not _is_valid_email(to):
        return {
            "success": False,
            "message": "Invalid recipient email address",
            "details": {"to": to},
        }

    msg = _build_message(to, subject, body, attachments)
    return await _send_message(msg)


async def send_daily_summary(to: str, summary_text: str) -> Dict[str, Any]:
    subject = "Daily Summary from BizGenie"
    body = f"Hello,\n\nHere is your daily summary:\n\n{summary_text}\n\nRegards,\nBizGenie"
    return await send_email(to, subject, body)


async def test_email() -> Dict[str, Any]:
    details = {
        "enabled": settings.EMAIL_MCP_ENABLED,
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "username": settings.EMAIL_USERNAME,
        "password_present": bool(settings.EMAIL_PASSWORD),
    }
    ok = all(
        [
            settings.EMAIL_MCP_ENABLED,
            settings.EMAIL_HOST,
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD,
        ]
    )
    message = "Email MCP configuration is valid" if ok else "Email MCP configuration incomplete"

    logger.info("email.test", **details)

    return {
        "success": ok,
        "message": message,
        "details": {**details, "password": _mask(settings.EMAIL_PASSWORD)},
    }
