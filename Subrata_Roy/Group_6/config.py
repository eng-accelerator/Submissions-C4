"""Application configuration loaded from environment."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# OpenRouter (primary LLM)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

# Embeddings (OpenAI-compatible; use OpenAI key or OpenRouter if supported)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# JIRA (strip whitespace/newlines so pasted values don't break URLs)
def _clean_env(s: str, default: str = "") -> str:
    return (s or default).strip().split("\n")[0].strip()


def _clean_project_key(s: str, default: str = "INCIDENT") -> str:
    """Take first line, then first token (JIRA keys are e.g. KAN, INCIDENT) so no \\n\\t or junk leaks into URL."""
    raw = (s or "").strip()
    first_line = raw.replace("\r", "\n").split("\n")[0].strip()
    # First token only (split on any whitespace including \t)
    parts = first_line.split()
    first_token = (parts[0] if parts else first_line).strip()
    # JIRA project keys are typically uppercase letters and numbers; strip any trailing non-alphanumeric
    if first_token:
        first_token = "".join(c for c in first_token if c.isalnum() or c in "-_") or first_token
    return first_token or default


JIRA_SERVER = _clean_env(os.getenv("JIRA_SERVER", ""))
JIRA_EMAIL = _clean_env(os.getenv("JIRA_EMAIL", ""))
JIRA_API_TOKEN = _clean_env(os.getenv("JIRA_API_TOKEN", ""))
JIRA_PROJECT_KEY = _clean_project_key(os.getenv("JIRA_PROJECT_KEY", "KAN")) or "INCIDENT"

# ChromaDB
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"))
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_LOGS_DIR = PROJECT_ROOT / "sample_logs"
