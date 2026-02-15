"""
utils/llm_client.py
====================
Unified LLM client wrapping OpenRouter's OpenAI-compatible API.

Features:
    - Automatic retry with exponential backoff (3 attempts)
    - Robust JSON parsing from LLM responses
    - Token usage tracking
    - Debug logging support

USAGE:
    from utils.llm_client import LLMClient
    client = LLMClient()
    response = client.chat("You are helpful.", "What is AI?")
    data = client.chat_json("Return JSON.", "List 3 fruits.")
"""

from __future__ import annotations

import json
import re
import logging
from typing import Optional

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Thread-safe LLM client for OpenRouter with retry logic and token tracking.

    Attributes:
        model: The default model to use for requests.
        total_tokens: Running total of tokens consumed.
        call_log: Per-call token usage records for detailed breakdown.
    """

    def __init__(self, model: Optional[str] = None):
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        self.model = model or settings.DEFAULT_MODEL
        self.total_tokens: int = 0
        self.call_log: list[dict] = []  # [{agent, prompt_tokens, completion_tokens, total_tokens}]
        self._current_agent: str = "unknown"  # Set by graph nodes before LLM calls

    def set_agent(self, agent_name: str):
        """Set the current agent label for token attribution."""
        self._current_agent = agent_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request to the LLM.

        Args:
            system_prompt: The system message defining the LLM's role.
            user_prompt: The user's message/query.
            model: Override the default model.
            temperature: Override the default temperature.
            max_tokens: Override the default max tokens.

        Returns:
            The LLM's response text.
        """
        model = model or self.model
        temperature = temperature if temperature is not None else settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS

        if settings.DEBUG_LLM:
            logger.debug(f"LLM Request [{model}]:\n  System: {system_prompt[:150]}...\n  User: {user_prompt[:150]}...")

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""

        if response.usage:
            prompt_tok = response.usage.prompt_tokens or 0
            completion_tok = response.usage.completion_tokens or 0
            total_tok = response.usage.total_tokens or (prompt_tok + completion_tok)
            self.total_tokens += total_tok
            self.call_log.append({
                "agent": self._current_agent,
                "prompt_tokens": prompt_tok,
                "completion_tokens": completion_tok,
                "total_tokens": total_tok,
            })
            logger.info(
                f"Tokens [{self._current_agent}]: {total_tok} "
                f"(prompt={prompt_tok}, "
                f"completion={completion_tok}) | "
                f"Running total: {self.total_tokens}"
            )

        if settings.DEBUG_LLM:
            logger.debug(f"LLM Response: {content[:300]}...")

        return content

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> dict:
        """
        Chat expecting a JSON response. Handles common LLM JSON formatting issues.

        Args:
            system_prompt: System message (will be enhanced with JSON instruction).
            user_prompt: User message.
            **kwargs: Passed to self.chat().

        Returns:
            Parsed JSON as a Python dict.

        Raises:
            ValueError: If JSON cannot be extracted from the response.
        """
        enhanced_system = (
            system_prompt
            + "\n\nCRITICAL: You MUST respond with valid JSON only. "
            "No markdown code fences, no explanatory text outside the JSON."
        )
        raw = self.chat(enhanced_system, user_prompt, **kwargs)
        return self._parse_json(raw)

    def get_usage_summary(self) -> dict:
        """
        Return a summary of token usage grouped by agent.

        Returns:
            Dict with per-agent breakdown and totals.
        """
        by_agent: dict[str, dict] = {}
        for entry in self.call_log:
            agent = entry["agent"]
            if agent not in by_agent:
                by_agent[agent] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}
            by_agent[agent]["prompt_tokens"] += entry["prompt_tokens"]
            by_agent[agent]["completion_tokens"] += entry["completion_tokens"]
            by_agent[agent]["total_tokens"] += entry["total_tokens"]
            by_agent[agent]["calls"] += 1
        return {
            "by_agent": by_agent,
            "total_tokens": self.total_tokens,
            "total_calls": len(self.call_log),
        }

    @staticmethod
    def _parse_json(text: str) -> dict:
        """
        Robustly extract JSON from LLM response text.

        Handles common issues:
        - Raw JSON (ideal case)
        - JSON wrapped in ```json ... ``` code blocks
        - JSON with leading/trailing text
        - JSON arrays (converted to {"items": [...]})

        Args:
            text: Raw LLM response text.

        Returns:
            Parsed JSON dict.

        Raises:
            ValueError: If no valid JSON can be extracted.
        """
        text = text.strip()

        # 1. Try direct parse
        try:
            result = json.loads(text)
            return result if isinstance(result, dict) else {"items": result}
        except json.JSONDecodeError:
            pass

        # 2. Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
        try:
            result = json.loads(cleaned)
            return result if isinstance(result, dict) else {"items": result}
        except json.JSONDecodeError:
            pass

        # 3. Extract JSON object with regex
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 4. Extract JSON array with regex
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                items = json.loads(match.group())
                return {"items": items}
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not parse JSON from LLM response. "
            f"First 500 chars: {text[:500]}"
        )
