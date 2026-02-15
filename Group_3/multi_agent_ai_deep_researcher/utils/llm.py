"""
LLM management for the Multi-Agent AI Deep Researcher using Pydantic models.

Handles initialization, configuration, and usage of LLMs via Ollama.
Provides streaming and non-streaming interfaces for LLM calls.

Features:
- Lazy initialization of LLM
- Configured model selection from settings
- Streaming support for real-time token generation
- Token counting for cost/performance tracking
- Fallback error handling
- Timeout management
"""

from typing import Iterator, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from langchain_ollama import OllamaLLM
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings
import sys
from pathlib import Path

# Avoid local package name collision with stdlib `logging`.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) in sys.path:
    sys.path.remove(str(_PROJECT_ROOT))
import logging  # stdlib logging
sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

# Global LLM instance (lazy loaded)
_llm_instance: Optional[OllamaLLM] = None


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class OllamaConnectionError(LLMError):
    """Raised when unable to connect to Ollama service."""
    pass


class LLMResponse(BaseModel):
    """Response from an LLM call."""
    
    model_config = ConfigDict(extra="allow")
    
    success: bool = Field(description="Whether the call succeeded")
    content: str = Field(default="", description="Response text")
    model: str = Field(description="Model used")
    input_tokens: int = Field(default=0, description="Input token count")
    output_tokens: int = Field(default=0, description="Output token count")
    error: Optional[str] = Field(default=None, description="Error message if failed")


def initialize_llm() -> OllamaLLM:
    """
    Initialize LLM connection to Ollama.
    
    Called automatically on first LLM use. Verifies Ollama is running
    and accessible at the configured base URL.
    
    Returns:
        OllamaLLM instance
    
    Raises:
        OllamaConnectionError: If cannot connect to Ollama
    """
    global _llm_instance
    
    if _llm_instance is not None:
        return _llm_instance
    
    try:
        logger.info(
            f"Initializing Ollama LLM with model '{settings.ollama_model}' "
            f"at {settings.ollama_base_url}"
        )
        
        _llm_instance = OllamaLLM(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            timeout=settings.ollama_timeout,
        )
        
        # Test connection with a simple call
        test_response = _llm_instance.invoke("Say 'ready' in one word")
        logger.info(f"Ollama connection successful: {test_response}")
        
        return _llm_instance
        
    except Exception as e:
        error_msg = (
            f"Failed to connect to Ollama at {settings.ollama_base_url} "
            f"with model '{settings.ollama_model}': {str(e)}"
        )
        logger.error(error_msg)
        raise OllamaConnectionError(error_msg) from e


def get_llm() -> OllamaLLM:
    """
    Get the LLM instance (singleton).
    
    Returns:
        OllamaLLM instance
    """
    return initialize_llm()


@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=settings.retry_wait_seconds, max=30),
    retry=retry_if_exception_type(Exception),
)
def call_llm(
    prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Call LLM with a prompt and return response as Pydantic model.
    
    Uses retry logic to handle transient failures.
    
    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
    
    Returns:
        Dict with success, content, model, and token counts
    
    Raises:
        LLMError: If LLM call fails
    """
    try:
        llm = get_llm()
        
        logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
        
        response = llm.invoke(prompt)
        
        input_tokens = count_tokens(prompt)
        output_tokens = count_tokens(response)
        
        logger.debug(f"LLM response length: {len(response)}")
        
        return LLMResponse(
            success=True,
            content=response,
            model=settings.ollama_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error=None,
        ).model_dump()
        
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        raise LLMError(f"LLM invocation failed: {str(e)}") from e


def stream_llm(
    prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> Iterator[str]:
    """
    Call LLM in streaming mode, yielding tokens as they arrive.
    
    Useful for real-time UI updates and streaming responses.
    
    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
    
    Yields:
        Token strings as they're generated
    
    Raises:
        LLMError: If streaming fails
    """
    try:
        llm = get_llm()
        
        logger.debug(f"Streaming LLM with prompt length: {len(prompt)}")
        
        # Use the stream method if available
        if hasattr(llm, 'stream'):
            for token in llm.stream(prompt):
                yield token
        else:
            # Fallback to regular invoke if streaming not available
            response = llm.invoke(prompt)
            yield response
            
    except Exception as e:
        logger.error(f"LLM streaming failed: {str(e)}")
        raise LLMError(f"LLM streaming failed: {str(e)}") from e


def format_messages_for_llm(messages: List[Dict[str, Any]]) -> str:
    """
    Convert message dicts to a string prompt for Ollama.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        Formatted prompt string
    """
    formatted = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "message")
            content = msg.get("content", "")
        else:
            role = getattr(msg, 'type', 'message')
            content = msg.content
        
        formatted.append(f"{role.upper()}: {content}")
    
    return "\n".join(formatted)


def count_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Simple heuristic: approximately 1 token per 4 characters.
    More accurate with actual tokenizer, but this avoids dependency.
    
    Args:
        text: Text to count tokens
    
    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ≈ 4 characters average
    return len(text) // 4


def estimate_llm_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Estimate cost of LLM call (for monitoring/analytics).
    
    For Ollama local models, cost is 0 (runs locally).
    This is a placeholder for future cloud model support.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name
    
    Returns:
        Estimated cost in USD (0 for Ollama)
    """
    # Ollama is free (runs locally)
    if "ollama" in model.lower() or settings.ollama_base_url.startswith("http://localhost"):
        return 0.0
    
    # Placeholder for future cloud pricing
    return 0.0


__all__ = [
    "initialize_llm",
    "get_llm",
    "call_llm",
    "stream_llm",
    "format_messages_for_llm",
    "count_tokens",
    "estimate_llm_cost",
    "LLMResponse",
    "LLMError",
    "OllamaConnectionError",
]
