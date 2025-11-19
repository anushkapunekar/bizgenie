"""
Application configuration loaded from environment variables.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


def _mask(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


class Config(BaseSettings):
    """Central application settings."""

    # WhatsApp
    WHATSAPP_MCP_ENABLED: bool = False
    WHATSAPP_API_URL: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_SENDER_NAME: Optional[str] = Field(default="BizGenie")

    # Email
    EMAIL_MCP_ENABLED: bool = False
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = Field(default=587)
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # Calendar
    CALENDAR_MCP_ENABLED: bool = False
    CALENDAR_SENDER_EMAIL: Optional[str] = None

    # API keys / auth
    API_SERVICE_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def masked_dict(self) -> Dict[str, Any]:
        """Return settings dict with sensitive fields masked."""
        data = self.model_dump()
        sensitive_fields = {
            "WHATSAPP_ACCESS_TOKEN",
            "EMAIL_PASSWORD",
            "API_SERVICE_KEY",
        }
        for field in sensitive_fields:
            if field in data:
                data[field] = _mask(data[field])
        return data

    def __repr__(self) -> str:  # pragma: no cover - diagnostic helper
        return f"Config({self.masked_dict()})"


@lru_cache
def get_settings() -> Config:
    settings = Config()
    logger.info("config.loaded", **settings.masked_dict())
    return settings

