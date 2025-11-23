"""
LLM Service using HuggingFace Inference API (Qwen2.5-7B-Instruct).
Stable, no LangChain, uses httpx only.
"""

import os
from typing import Optional

import httpx
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


class LLMService:
    """Service for LLM inference using HuggingFace Inference API."""

    def __init__(self):
        # Force HuggingFace provider only
        self.provider = "huggingface"

        # Support both old and new env variable names
        self.model_name = (
            os.getenv("HF_MODEL")
            or os.getenv("LLM_MODEL")
            or "Qwen/Qwen2.5-7B-Instruct"
        )

        # Try HF_API_KEY first, then fallback to old HUGGINGFACE_API_KEY
        self.hf_api_key = (
            os.getenv("HF_API_KEY")
            or os.getenv("HUGGINGFACE_API_KEY")
            or ""
        )

        if not self.hf_api_key:
            logger.error("HF_API_KEY / HUGGINGFACE_API_KEY is missing! Add it to .env")

        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.headers = {"Authorization": f"Bearer {self.hf_api_key}"} if self.hf_api_key else {}

        logger.info(
            "LLM Service initialized",
            provider="huggingface",
            model=self.model_name,
        )

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate text using HuggingFace Inference API.
        Returns clean generated text or a fallback message.
        """

        # Build final prompt: your RAG prompt already includes docs & tool instructions,
        # so we just pass it through. If you WANT extra context, you can prepend it.
        if context:
            full_prompt = f"Context:\n{context}\n\nUser message:\n{prompt}\n\nAnswer:"
        else:
            full_prompt = prompt

        if not self.hf_api_key:
            logger.error("No HF API key set, using fallback")
            return self._fallback(prompt, context)

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.4,
                "top_p": 0.95,
                "repetition_penalty": 1.05,
            },
        }

        try:
            logger.info("llm.request", model=self.model_name, url=self.api_url)

            with httpx.Client(timeout=80.0) as client:
                response = client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                )

            if response.status_code != 200:
                logger.error(
                    "llm.api_error",
                    status=response.status_code,
                    body=response.text[:500],
                )
                return self._fallback(prompt, context)

            data = response.json()

            # HuggingFace text-generation usually returns:
            # [ { "generated_text": "...full prompt + completion..." } ]
            text = ""

            if isinstance(data, list) and data and isinstance(data[0], dict):
                if "generated_text" in data[0]:
                    text = data[0]["generated_text"]
                else:
                    text = str(data[0])
            elif isinstance(data, dict) and "generated_text" in data:
                text = data["generated_text"]
            else:
                # Last fallback: just stringify whatever we got
                text = str(data)

            if not isinstance(text, str):
                text = str(text)

            # Many HF models echo the prompt. If our prompt contains "ANSWER:" or "Answer:",
            # try to cut the output after that marker so user doesn't see the whole prompt.
            for marker in ["ANSWER:", "Answer:", "Answer:", "answer:"]:
                if marker in text:
                    text = text.split(marker, 1)[-1].strip()
                    break

            clean = text.strip()
            if not clean:
                logger.warning("llm.empty_response", raw=data)
                return self._fallback(prompt, context)

            return clean

        except Exception as e:
            logger.error("llm.exception", error=str(e))
            return self._fallback(prompt, context)

    def _fallback(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Fallback message when HF API fails.
        Make it *less* like an error and more like a simple generic reply.
        """
        if context:
            return (
                "I'm having trouble reaching the AI model right now, "
                "but based on your documents I can say this is related to your business context. "
                "You can also contact the business directly for precise details."
            )

        return (
            "I'm having a little trouble processing this right now on the AI side, "
            "but your message has been received. You can try asking again or contact us directly."
        )


# Global singleton instance
llm_service = LLMService()
