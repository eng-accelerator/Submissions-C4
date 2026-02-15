# 🧠 Smart Medical Research Assistant

A production-grade AI application that performs **deep medical research** using a 5-agent LangGraph pipeline. Research results are persisted as a vector database, enabling users to interactively query previously generated reports through a dedicated chat interface.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Knowledge Base & RAG](#knowledge-base--rag)
- [Frontend Interface](#frontend-interface)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [How It Works — End to End](#how-it-works--end-to-end)

---

## Overview

The Smart Medical Research Assistant accepts a natural-language medical research question, automatically researches it across multiple peer-reviewed and live data sources, critically validates the evidence, synthesizes hypotheses and emerging trends, and produces a structured citation-backed report. Approved reports are saved as `.docx` files and automatically indexed into a LanceDB vector database, which powers a RAG-based chat interface for querying past research.

---

## Architecture

The application is composed of three modules:

```
multi-agent.py   ←→   front-end.py   ←→   rag.py
     │                     │                  │
LangGraph pipeline    Gradio UI          LanceDB + LangChain
5 specialized agents  Web interface      Vector store & RAG chain
```

### High-Level Flow

```
User Query
    │
    ▼
[1] Validate Query ──► OUT OF SCOPE → END
    │
    ▼
[2] Contextual Retriever (PubMed + NewsAPI + Tavily)
    │
    ▼
[3] Critical Analysis ──► Low Confidence? → Retry [2] (max 2 retries)
    │
    ▼
[4] Insight Generation (hypotheses + trends)
    │
    ▼
[5] Report Builder → Structured Report
    │
    ▼
User Approves → Saved as .docx + Indexed into Vector DB
    │
    ▼
Knowledge Base Chat Interface (RAG)
```

---

## Agent Pipeline

The pipeline is built with **LangGraph** and orchestrates five specialized agents that share a typed state object (`AgentState`).

### Agent Flow Diagram

![Agent Workflow](Agent-Workflow.png)

### State Schema

| Field | Type | Description |
|---|---|---|
| `user_query` | `str` | Original research question |
| `is_valid_query` | `bool` | Set by Validation Agent — gates the pipeline |
| `context_data` | `dict` | Raw data from PubMed, NewsAPI, Tavily |
| `retry_count` | `int` | Tracks retrieval retry attempts (max 2) |
| `critic_summary` | `dict` | Scored sources, confidence metrics |
| `insight_summary` | `str` | ~1000-word narrative synthesized from evidence |
| `final_report` | `dict` | Fully structured Pydantic-validated report |

### Agent 1 — Query Validator (`validate_user_query_node`)

Determines whether the query is within scope (medical research, clinical studies, pharmacology). Out-of-scope queries terminate the pipeline immediately. Uses GPT-5 Nano via OpenRouter.

### Agent 2 — Contextual Retriever (`contextual_retriever_node`)

Fetches evidence from three external sources **in parallel** using `ThreadPoolExecutor`:

- **PubMed** — peer-reviewed biomedical literature via NCBI E-utilities API
- **NewsAPI** — recent medical/health news articles
- **Tavily** — live web search with AI-powered relevance filtering

### Agent 3 — Critical Analysis (`critical_analysis_node`)

Validates source quality using **ScienceDirect API** and scores each source across three dimensions:

- **Recency score** — based on publication date (0.0–1.0)
- **Affirmation score** — relevance to the query (0.0–1.0)
- **Domain authority** — heuristic credibility score (0.0–1.0)

If the weighted average confidence falls below `0.3`, the agent triggers a retry loop back to Agent 2. Maximum of 2 retry attempts before proceeding with an uncertainty disclaimer.

### Agent 4 — Insight Generation (`insight_generation_node`)

Uses chain-of-thought reasoning to synthesize the validated evidence into:

- Emerging trends in the research area
- Testable scientific hypotheses with confidence scores
- Identified research gaps

### Agent 5 — Report Builder (`report_builder_node`)

Assembles the final structured output as a **Pydantic-validated `FinalReport`** containing:

- Executive summary (200–300 words)
- Detailed breakdown (~2700 words)
- Full citation list with per-source scoring
- Research gaps (Critical / Moderate / Minor)
- Hypotheses with rationale and confidence scores
- Emerging trends with clinical implications
- Overall confidence score and optional uncertainty disclaimer

---

## Knowledge Base & RAG

Managed by `rag.py` using **LangChain** and **LanceDB**.

### Persistence Flow

1. User reviews and approves the generated report in the UI
2. Report is saved as a timestamped `.docx` file in the `reports/` directory
3. `chunk_and_vectorize()` is called — loads all documents in `reports/`, splits them into 512-token chunks (50-token overlap), and embeds them using `text-embedding-3-small` via OpenRouter
4. The LanceDB vector store (`rag_vectordb/`) is rebuilt (existing DB is replaced)

### RAG Query Flow

When a user submits a query to the Knowledge Base chat:

1. The query is embedded and similarity-searched against the vector store
2. Relevant chunks are retrieved via LangChain's retriever interface
3. A GPT-4o-mini LLM (via OpenRouter) generates a grounded answer using only the retrieved context
4. The answer is streamed back to the UI

### Configuration (`rag.py`)

| Parameter | Value |
|---|---|
| Embedding model | `text-embedding-3-small` |
| LLM | `openai/gpt-4o-mini` (via OpenRouter) |
| Chunk size | 512 tokens |
| Chunk overlap | 50 tokens |
| Vector store | LanceDB (`rag_vectordb/` directory) |
| Supported formats | `.pdf`, `.docx`, `.doc`, `.txt` |

---

## Frontend Interface

Built with **Gradio 4+**, the UI (`front-end.py`) provides a split-panel interface.

![App Screenshot](App.png)

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│            SMART MEDICAL RESEARCH ASSISTANT          [🌙]   │
├─────────────────────────────────┬───────────────────────────┤
│  Agent Response                 │  Knowledge Base Response  │
│  (executive summary + report)   │  (RAG chat output)        │
│                                 │                           │
│  Agent Execution Log            │                           │
│  (live stdout stream)           │                           │
├─────────────────────────────────┼───────────────────────────┤
│  Your Query          [text]     │  KB Query        [text]   │
├─────────────────────────────────┼───────────────────────────┤
│  [Submit]  [Approve]            │  [↑ Search KB]            │
│  Status message                 │                           │
└─────────────────────────────────┴───────────────────────────┘
```

### UI Features

- **Submit** — runs the full 5-agent pipeline; streams responses and logs in real time
- **Approve** — saves the generated report as a `.docx` file and rebuilds the vector DB
- **Knowledge Base Query** — queries previously approved research using the RAG chain
- **Dark/Light mode toggle** — client-side CSS class toggle, no page reload
- Approve button is disabled until a pipeline run completes, preventing premature saves

---

## Project Structure

```
.
├── multi-agent.py       # LangGraph 5-agent research pipeline
├── front-end.py         # Gradio UI — main entry point
├── rag.py               # LanceDB vector store + LangChain RAG chain
├── reports/             # Auto-created: approved .docx research reports
├── rag_vectordb/        # Auto-created: LanceDB vector database
└── .env                 # API keys (see Environment Variables)
```

---

## Prerequisites

- Python 3.10+
- Node.js (optional, only if generating `.docx` files via `docx-js`)
- API keys for all required services (see below)

---

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd smart-medical-research-assistant

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install gradio>=4.0 \
            gradio-rich-textbox \
            python-dotenv \
            python-docx \
            lancedb \
            langchain-openai \
            langchain-community \
            langchain-core \
            langchain-text-splitters \
            langgraph>=0.2 \
            pydantic>=2.0 \
            requests \
            tavily-python \
            rich \
            unstructured

# 4. Copy and populate the environment file
cp .env.example .env
# Edit .env with your API keys
```

---

## Environment Variables

Create a `.env` file in the project root with the following keys:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional but recommended (missing keys degrade source coverage)
PUBMED_API_KEY=your_ncbi_pubmed_api_key
NEWS_API_KEY=your_newsapi_org_api_key
TAVILY_API_KEY=your_tavily_api_key
SCIENCE_DIRECT_API_KEY=your_elsevier_sciencedirect_api_key
```

| Key | Source | Required |
|---|---|---|
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) | ✅ Yes |
| `PUBMED_API_KEY` | [NCBI API Keys](https://www.ncbi.nlm.nih.gov/account/) | Recommended |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Recommended |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Recommended |
| `SCIENCE_DIRECT_API_KEY` | [Elsevier Dev Portal](https://dev.elsevier.com) | Recommended |

---

## Usage

### Launch the Web Interface

```bash
python front-end.py
```

The app will be available at `http://127.0.0.1:7860`.

### Run the Agent Pipeline via CLI (no UI)

```bash
python multi-agent.py --query "What are the latest treatments for treatment-resistant depression?"
```

### Run the RAG Engine via CLI

```bash
# Index documents in reports/ and query the vector DB
python rag.py "What did the research say about SSRIs?"
```

---

## How It Works — End to End

1. **User enters a medical research question** in the "Your Query" field and clicks Submit.
2. The **Validation Agent** checks that the query is within the medical research domain.
3. The **Contextual Retriever** fetches literature from PubMed, recent news from NewsAPI, and web results from Tavily, running all three in parallel.
4. The **Critical Analysis Agent** scores each source for recency, relevance, and authority. If overall confidence is below 0.3, retrieval is retried up to 2 times with refined parameters.
5. The **Insight Generation Agent** synthesizes the validated evidence into hypotheses, emerging trends, and identified gaps using chain-of-thought reasoning.
6. The **Report Builder Agent** assembles everything into a structured Pydantic report with an executive summary, detailed breakdown, and full citation list.
7. The report is displayed in the UI. The user can review it and click **Approve**.
8. On approval, the report is saved as a timestamped `.docx` file in `reports/` and the LanceDB vector database is rebuilt to include the new content.
9. The user can then type questions into the **Knowledge Base Query** panel to retrieve grounded answers from all previously approved research.
