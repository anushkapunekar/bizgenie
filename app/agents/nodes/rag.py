"""
Resilient RAG node for BizGenie (NO external LLM).

- Uses vector store when available
- Falls back to business metadata if vector store fails or finds nothing
- ALWAYS returns a plain text answer
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from app.rag.vectorstore import vector_store

logger = structlog.get_logger(__name__)


def _format_documents(documents: List[Dict[str, Any]], limit: int = 3) -> str:
    formatted: List[str] = []
    for idx, doc in enumerate(documents[:limit], start=1):
        text = (doc.get("text") or "").strip()
        if not text:
            continue
        meta = doc.get("metadata") or {}
        src = meta.get("filename") or meta.get("source") or "Document"
        formatted.append(f"[{idx}] From {src}:\n{text}")
    return "\n\n".join(formatted)


def _fallback_from_metadata(user_message: str, meta: Dict[str, Any]) -> str:
    name = meta.get("name") or "this business"
    description = meta.get("description") or ""
    services = meta.get("services") or []
    hours = meta.get("working_hours") or {}
    contact_email = meta.get("contact_email") or ""
    contact_phone = meta.get("contact_phone") or ""

    parts: List[str] = []

    parts.append(f"Thanks for your message! Here's what I can tell you about {name} right now:")

    if description:
        parts.append(f"\n• About us: {description}")

    if services:
        if isinstance(services, list):
            s = ", ".join(services)
        else:
            s = str(services)
        parts.append(f"\n• Services we offer: {s}")

    if hours:
        parts.append("\n• Working hours:")
        for d, info in hours.items():
            if info and info.get("open") and info.get("close"):
                parts.append(f"  - {d.capitalize()}: {info['open']} – {info['close']}")

    if contact_email or contact_phone:
        parts.append("\n• You can contact us at:")
        if contact_email:
            parts.append(f"  - Email: {contact_email}")
        if contact_phone:
            parts.append(f"  - Phone/WhatsApp: {contact_phone}")

    parts.append(
        f"\nYou asked: “{user_message}”. "
        f"If you want, you can ask about services, pricing, or booking an appointment."
    )

    return "\n".join(parts)


def _build_answer_from_docs(user_message: str, meta: Dict[str, Any], documents: List[Dict[str, Any]]) -> str:
    name = meta.get("name") or "this business"
    docs_block = _format_documents(documents)

    if not docs_block:
        return _fallback_from_metadata(user_message, meta)

    return (
        f"Here’s what I can tell you about {name} based on our documents:\n\n"
        f"{docs_block}\n\n"
        f"If you need something more specific, try asking a more detailed question."
    )


def generate_answer(
    *,
    business_id: int,
    user_message: str,
    n_results: int = 5,
    metadata_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    meta: Dict[str, Any] = metadata_context or {}
    documents: List[Dict[str, Any]] = []

    # Vector store query
    try:
        documents = vector_store.query_documents(
            business_id=business_id,
            query=user_message,
            n_results=n_results,
        )
        logger.info(
            "rag.query_completed",
            business_id=business_id,
            results=len(documents),
            query=user_message,
        )
    except Exception as exc:
        logger.error("rag.vectorstore_failed", error=str(exc))
        documents = []

    # Build answer
    if documents:
        reply = _build_answer_from_docs(user_message, meta, documents)
    else:
        reply = _fallback_from_metadata(user_message, meta)

    return {
        "reply": reply,
        "documents_used": len(documents),
        "metadata_context": meta,
    }
