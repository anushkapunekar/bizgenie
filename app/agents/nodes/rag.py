"""
Minimal RAG node: always query vector store, always answer with docs if present.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from app.llm_service import llm_service
from app.rag.vectorstore import vector_store

logger = structlog.get_logger(__name__)


def _format_documents(documents: List[Dict[str, Any]]) -> str:
    """Turn retrieved chunks into a readable block for the prompt."""
    formatted = []
    for idx, doc in enumerate(documents, start=1):
        metadata = doc.get("metadata") or {}
        source = metadata.get("filename") or metadata.get("source") or "Document"
        chunk_text = doc.get("text", "").strip()
        formatted.append(f"[{idx}] Source: {source}\n{chunk_text}")
    return "\n\n".join(formatted)


def _build_prompt(user_message: str, documents: List[Dict[str, Any]]) -> str:
    if documents:
        docs_block = _format_documents(documents)
        prompt = (
            "You are BizGenie, an expert assistant for small businesses.\n"
            "Use ONLY the following document extracts to answer.\n"
            "If the documents contradict each other, pick the most recent or most detailed section.\n\n"
            f"{docs_block}\n\n"
            f"User question: {user_message}\n\n"
            "Give a concise, confident answer that cites the relevant details."
        )
    else:
        prompt = (
            "You are BizGenie, an expert assistant for small businesses.\n"
            "No company documents matched this query, so answer using general business knowledge.\n\n"
            f"User question: {user_message}\n\n"
            "Provide a helpful, on-topic answer."
        )
    return prompt


def generate_answer(
    *,
    business_id: int,
    user_message: str,
    n_results: int = 5,
    metadata_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Main RAG routine. Returns dict with reply + debug info."""
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

    prompt = _build_prompt(user_message, documents)
    logger.debug("rag.prompt_built", business_id=business_id, prompt_preview=prompt[:400])

    response_text = llm_service.generate(prompt)
    logger.info(
        "rag.llm_completed",
        business_id=business_id,
        has_docs=bool(documents),
        response_preview=response_text[:200],
    )

    return {
        "reply": response_text.strip(),
        "documents_used": len(documents),
        "metadata_context": metadata_context or {},
    }