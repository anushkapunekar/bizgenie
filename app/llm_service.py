"""
Free LLM service using Ollama or Hugging Face.
"""
import os
from typing import Optional, Dict, Any
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger(__name__)


class LLMService:
    """Service for free LLM inference using Ollama or Hugging Face."""
    
    def __init__(self):
        """Initialize LLM service based on configuration."""
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.model_name = os.getenv("LLM_MODEL", "llama3.2")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
        logger.info(
            "LLM Service initialized",
            provider=self.provider,
            model=self.model_name
        )
    
    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: User prompt/question
            context: Optional context (e.g., retrieved documents)
        
        Returns:
            Generated response
        """
        try:
            if self.provider == "ollama":
                return self._generate_ollama(prompt, context)
            elif self.provider == "huggingface":
                return self._generate_huggingface(prompt, context)
            else:
                logger.warning("Unknown LLM provider, using fallback", provider=self.provider)
                return self._generate_fallback(prompt, context)
        except Exception as e:
            logger.error("Error generating LLM response", error=str(e))
            return self._generate_fallback(prompt, context)
    
    def _generate_ollama(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate using Ollama (local, completely free)."""
        try:
            import httpx
            
            # Build full prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"""Context from documents:
{context}

Question: {prompt}

Answer based on the context above:"""
            
            # Call Ollama API
            response = httpx.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "").strip()
        except ImportError:
            logger.error("httpx not installed. Install with: pip install httpx")
            return self._generate_fallback(prompt, context)
        except Exception as e:
            logger.error("Ollama generation error", error=str(e))
            return self._generate_fallback(prompt, context)
    
    def _generate_huggingface(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate using Hugging Face Inference API (free tier available)."""
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            from langchain_core.prompts import PromptTemplate
            
            # Build prompt template
            if context:
                template = """Context from documents:
{context}

Question: {question}

Answer based on the context above:"""
                prompt_template = PromptTemplate(
                    input_variables=["context", "question"],
                    template=template
                )
                full_prompt = prompt_template.format(context=context, question=prompt)
            else:
                full_prompt = prompt
            
            # Use Hugging Face endpoint
            llm = HuggingFaceEndpoint(
                repo_id=self.model_name,
                huggingfacehub_api_token=self.hf_api_key if self.hf_api_key else None,
                temperature=0.7,
                max_length=512
            )
            
            response = llm.invoke(full_prompt)
            return response.strip()
        except ImportError:
            logger.error("langchain-huggingface not installed")
            return self._generate_fallback(prompt, context)
        except Exception as e:
            logger.error("Hugging Face generation error", error=str(e))
            return self._generate_fallback(prompt, context)
    
    def _generate_fallback(self, prompt: str, context: Optional[str] = None) -> str:
        """Fallback simple response generation."""
        if context:
            # Return first part of context as answer
            return f"Based on the available information:\n\n{context[:500]}..."
        return "I'm processing your request. Please contact us directly for more detailed information."


# Global LLM service instance
llm_service = LLMService()

