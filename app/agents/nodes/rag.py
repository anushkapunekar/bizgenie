"""
Resilient RAG node for BizGenie.

- Uses vector store + LLM when available
- Falls back to business metadata if LLM/vector store fail
- Returns plain text by default (tool JSON optional)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from app.llm_service import llm_service
from app.rag.vectorstore import vector_store

logger = structlog.get_logger(__name__)


def _format_documents(documents: List[Dict[str, Any]]) -> str:
    formatted = []
    for idx, doc in enumerate(documents, start=1):
        text = (doc.get("text") or "").strip()
        if not text:
            continue
        meta = doc.get("metadata") or {}
        src = meta.get("filename") or meta.get("source") or "Document"
        formatted.append(f"[{idx}] Source: {src}\n{text}")
    return "\n\n".join(formatted)


def _fallback_from_metadata(user_message: str, meta: Dict[str, Any]) -> str:
    """Used when vectorstore or LLM fail."""
    name = meta.get("name") or "this business"
    services = meta.get("services") or []
    hours = meta.get("working_hours") or {}

    parts = [f"I'm having a bit of trouble generating a full answer right now, but here’s what I can share about {name}:"]

    if services:
        s = ", ".join(services) if isinstance(services, list) else str(services)
        parts.append(f"\n• Services offered: {s}")

    if hours:
        parts.append("\n• Working hours:")
        for d, info in hours.items():
            if info and info.get("open") and info.get("close"):
                parts.append(f"  - {d.capitalize()}: {info['open']}–{info['close']}")

    parts.append("\nYou can rephrase your question and I will try again.")
    return "\n".join(parts)


def _build_prompt(user_message: str, documents: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    docs_text = _format_documents(documents) if documents else "No matching documents."

    return f"""
You are BizGenie, an assistant for small businesses.

BUSINESS INFO:
{meta}

DOCUMENTS:
{docs_text}

GUIDELINES:
- Answer naturally in plain text.
- DO NOT return JSON unless you are **very sure** the user wants an email, WhatsApp message, or appointment action.
- For normal questions about services, pricing, hours, etc → plain text answer.

USER MESSAGE:
{user_message}

Now give the best possible helpful answer.
"""


def generate_answer(
    *,
    business_id: int,
    user_message: str,
    n_results: int = 5,
    metadata_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    meta = metadata_context or {}
    documents: List[Dict[str, Any]] = []

    # Try vectorstore
    try:
        documents = vector_store.query_documents(
            business_id=business_id,
            query=user_message,
            n_results=n_results,
        )
    except Exception as exc:
        logger.error("rag.vectorstore_failed", error=str(exc))
        documents = []

    prompt = _build_prompt(user_message, documents, meta)

    # Try LLM
    try:
        reply = llm_service.generate(prompt).strip()
        if not reply:
            reply = _fallback_from_metadata(user_message, meta)
    except Exception as exc:
        logger.error("rag.llm_failed", error=str(exc))
        reply = _fallback_from_metadata(user_message, meta)

    return {
        "reply": reply,
        "documents_used": len(documents),
        "metadata_context": meta,
    }
