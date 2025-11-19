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
    """
    Tool-aware BizGenie prompt.
    Ensures model outputs either:
    - Natural language answer, OR
    - JSON with call_tool instructions.
    """

    docs_block = _format_documents(documents) if documents else "No matching documents."

    return f"""
You are BizGenie, an AI assistant for small businesses.
You can answer questions OR call tools to perform actions.

TOOLS YOU CAN CALL:
1. WhatsApp Tools:
   - send_whatsapp
   - send_whatsapp_confirmation
   - send_whatsapp_update
   - send_whatsapp_cancellation
   - send_whatsapp_followup

2. Email Tools:
   - send_email
   - send_email_confirmation
   - send_email_update
   - send_email_cancellation
   - send_email_reminder
   - send_email_followup

3. Calendar Tools:
   - create_event
   - update_event
   - cancel_event

RULES FOR TOOL CALLS:
- If the user wants to book, schedule, reserve, or confirm an appointment → use create_event.
- If the user wants to reschedule or change the time → use update_event.
- If the user wants to cancel an appointment → use cancel_event.
- If the user wants a reminder → use send_email_reminder or send_whatsapp.
- If the user wants follow-up → pick the correct WhatsApp or Email follow-up tool.
- ALWAYS output valid JSON when calling a tool.
- JSON format MUST be:

{{
  "answer": "Your natural language response here",
  "call_tool": {{
        "name": "tool_name_here",
        "params": {{ ... }}
  }}
}}

- If no tool is needed, respond with only natural language and NO JSON.

CONTEXT DOCUMENTS (use them if relevant):
{docs_block}

USER MESSAGE:
{user_message}

INSTRUCTIONS:
- Decide whether the user message needs a tool.
- If a tool is needed, return ONLY JSON in the exact format above.
- If no tool is needed, respond normally.
Do NOT invent tools. Only use the listed tools.
"""

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