"""
OpenRouter LLM Client
━━━━━━━━━━━━━━━━━━━
Uses OpenRouter's OpenAI-compatible API so you can use any model
(GPT-4, Claude, Llama, etc.) with one key. Like having one bank card
that works at every ATM.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable, Tuple
import logging
import config

_client = None
_usage_callback: Optional[Callable[[Dict[str, Any]], None]] = None
_current_agent_id: str = "unknown"
logger = logging.getLogger(__name__)

# Estimated prices in USD per 1K tokens (input, output).
# Used for transparent cost tracking in the UI.
_MODEL_PRICING_PER_1K: Dict[str, Tuple[float, float]] = {
    "openai/gpt-4o-mini": (0.00015, 0.00060),
    "openai/gpt-4o": (0.00250, 0.01000),
}


def _get_client():
    """Lazy-init OpenAI client pointed at OpenRouter."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )
    return _client


def is_available() -> bool:
    """Return True if OpenRouter is configured (API key set)."""
    return bool(config.OPENROUTER_API_KEY and config.OPENROUTER_API_KEY.strip())


def set_tracking_callback(callback: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    """Register a callback to receive token/cost usage events."""
    global _usage_callback
    _usage_callback = callback


def set_current_agent(agent_id: Optional[str]) -> None:
    """Set current agent context for usage attribution."""
    global _current_agent_id
    _current_agent_id = agent_id or "unknown"


def clear_tracking() -> None:
    """Reset usage callback and current agent context."""
    global _usage_callback, _current_agent_id
    _usage_callback = None
    _current_agent_id = "unknown"


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Send a chat completion request to OpenRouter.
    messages: [{"role": "user"|"system"|"assistant", "content": "..."}]
    Returns the assistant's reply text, or None on error or if not configured.
    """
    if not is_available():
        return None

    model = model or config.LLM_MODEL

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice = resp.choices[0] if resp.choices else None
        output_text = choice.message.content.strip() if choice and choice.message and choice.message.content else None

        usage = getattr(resp, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or 0)
        cost_usd = _estimate_cost_usd(model, prompt_tokens, completion_tokens)

        if _usage_callback:
            _usage_callback(
                {
                    "agent_id": _current_agent_id,
                    "model": model,
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost_usd,
                }
            )

        if output_text:
            return output_text
        return None
    except Exception as exc:
        logger.warning("OpenRouter chat completion failed: %s", exc, exc_info=config.DEBUG)
        return None


def _estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate call cost using per-model token rates."""
    in_rate, out_rate = _MODEL_PRICING_PER_1K.get(model, (0.00050, 0.00150))
    return (input_tokens / 1000.0) * in_rate + (output_tokens / 1000.0) * out_rate
