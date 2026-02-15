"""
Configuration for Astraeus — Multi-Agent AI Deep Researcher.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Vector DB ──────────────────────────────────────────────────────────────
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")          # "chroma" only for v1
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "research_docs")

# ── Embedding Model ───────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")  # sentence-transformers model
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# ── LLM (OpenRouter) ───────────────────────────────────────────────────
# OpenRouter: one API for many models (GPT-4, Claude, etc.)
OPENROUTER_API_KEY = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("OPEN_ROUTER_API_KEY")
    or os.getenv("OPEN_ROUTER_API")
    or ""
)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")  # OpenRouter model id
LLM_PROVIDER = "openrouter"  # only openrouter for v1

# ── Tavily (optional web search for research) ────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Pipeline ──────────────────────────────────────────────────────────────
MAX_QUERY_EXPANSIONS = int(os.getenv("MAX_QUERY_EXPANSIONS", "3"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "10"))
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"
UPLOAD_CHUNK_SIZE = int(os.getenv("UPLOAD_CHUNK_SIZE", "900"))
UPLOAD_CHUNK_OVERLAP = int(os.getenv("UPLOAD_CHUNK_OVERLAP", "150"))
TOKEN_TRACKING_ENABLED = os.getenv("TOKEN_TRACKING_ENABLED", "true").lower() == "true"

# ── App ───────────────────────────────────────────────────────────────────
APP_TITLE = "Astraeus"
APP_TAGLINE = "Multi-Agent AI Deep Researcher · 6 Agents · RAG-Powered"
DEMO_TIMEOUT_SECONDS = int(os.getenv("DEMO_TIMEOUT_SECONDS", "180"))
APP_ENV = os.getenv("APP_ENV", "dev").lower()  # dev|staging|prod
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SHOW_TRACEBACK = os.getenv("SHOW_TRACEBACK", "false").lower() == "true"

# ── Upload safety limits (defense against oversized files) ───────────────
MAX_UPLOAD_FILE_MB = int(os.getenv("MAX_UPLOAD_FILE_MB", "15"))
MAX_UPLOAD_TOTAL_MB = int(os.getenv("MAX_UPLOAD_TOTAL_MB", "40"))
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "120"))

# ── Agent definitions (order matters) ─────────────────────────────────────
AGENTS = [
    {
        "id": "coordinator",
        "name": "Research Coordinator",
        "icon": "🤖",
        "subtitle": "Orchestrates the mission",
        "badge_icon": "🎯",
        "color": "#f472b6",
    },
    {
        "id": "retriever",
        "name": "Contextual Retriever",
        "icon": "🤖",
        "subtitle": "Pulls context from memory",
        "badge_icon": "🗄️",
        "color": "#06b6d4",
    },
    {
        "id": "critical_analysis",
        "name": "Critical Analysis",
        "icon": "🤖",
        "subtitle": "Challenges assumptions",
        "badge_icon": "🔎",
        "color": "#a78bfa",
    },
    {
        "id": "fact_checker",
        "name": "Fact-Checker",
        "icon": "🤖",
        "subtitle": "Verifies every claim",
        "badge_icon": "✅",
        "color": "#10b981",
    },
    {
        "id": "insight_generator",
        "name": "Insight Generator",
        "icon": "🤖",
        "subtitle": "Finds hidden opportunities",
        "badge_icon": "💡",
        "color": "#fbbf24",
    },
    {
        "id": "report_builder",
        "name": "Report Builder",
        "icon": "🤖",
        "subtitle": "Builds decision-ready output",
        "badge_icon": "📄",
        "color": "#3b82f6",
    },
]
