"""LangChain LLM configured for OpenRouter API."""
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def get_llm(temperature: float = 0.2, model: str | None = None):
    """Return a ChatOpenAI instance configured for OpenRouter."""
    return ChatOpenAI(
        model=model or OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
    )
