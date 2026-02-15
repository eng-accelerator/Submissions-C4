# Astraeus - Multi-Agent AI Deep Researcher

**An autonomous AI research assistant powered by specialized agents, RAG, and real-time collaboration**

```
┌──────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│ Coordinator  │──▶│  Retriever   │──▶│ Critical Check │──▶│ Fact Checker │──▶│ Insight Engine │──▶│ Report Builder│
└──────────────┘   └──────────────┘   └────────────────┘   └──────────────┘   └────────────────┘   └──────────────┘
       Query            Sources + RAG     Contradictions      Verification      Patterns + Gaps     Final Dossier
```

## Overview

Astraeus is a multi-agent AI research system that plans, investigates, and synthesizes knowledge autonomously.

Modern research is hard for one simple reason: the truth is scattered. Teams must manually combine academic references, live web results, technical docs, and contradictory viewpoints. This is slow, expensive, and vulnerable to confirmation bias.

Astraeus solves this with a sequential swarm of 6 specialized agents. Each agent has a clear role (orchestration, retrieval, analysis, verification, insight generation, and reporting), and each stage adds structured output to a shared pipeline state. Think of it like a banking approval flow: each desk adds checks before the next desk signs off.

The key innovation is not just "ask an LLM and hope." This project demonstrates practical AI engineering patterns: agent orchestration, retrieval-augmented generation (RAG), multi-source evidence handling, contradiction detection, transparent confidence scoring, and real-time cost/token observability.

## Key Features

- **6 Specialized AI Agents** working in sequence with shared pipeline state
- **Multi-Vector Database RAG** architecture (local vector store; extensible to Pinecone/Weaviate/Chroma/Qdrant)
- **Multi-source retrieval** combining indexed docs with live web search via Tavily
- **Contradiction detection** and source credibility scoring
- **Automated insights** including theme clustering, hypothesis generation, and knowledge-gap detection
- **Real-time token and cost tracking** per agent with budget-aware operation
- **Live animated pipeline visualization** with state transitions and per-agent progress
- **Post-run analytics** panels (embedding space, retrieval waterfall, claims-evidence)
- **Decision-ready markdown report** with citations and downloadable output

## Technical Innovations

- **Custom agent orchestration pipeline** with state machine flow (LangGraph-inspired)
- **Reciprocal-rank fusion** for multi-query retrieval across heterogeneous sources
- **Tiered credibility scoring** mapping source types to reliability weights
- **Semantic conflict heuristics** for contradiction detection without fine-tuned models
- **Per-agent telemetry** providing full cost/token/latency observability per pipeline stage

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Core** | Python 3.10+, Streamlit |
| **AI/LLM** | OpenRouter (multi-model gateway), Claude/GPT via OpenRouter, sentence-transformers (all-MiniLM-L6-v2) |
| **RAG** | Local persistent vector store (NumPy + JSON), multi-query retrieval, reciprocal-rank fusion, Tavily web search |
| **Analytics** | NumPy, Pandas, scikit-learn, Plotly |
| **Extensible** | LangChain/LangGraph, LlamaIndex, Pinecone/Weaviate/Chroma/Qdrant connectors |

## Setup

### Prerequisites

- Python 3.10+
- pip
- Git

### Installation

```bash
# Clone the repository
git clone <REPO_URL>
cd Astraeus-Multi-Agent-AI-Researcher

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM access |
| `TAVILY_API_KEY` | Optional | Tavily API key for live web search |
| `LLM_MODEL` | No | Model ID (default: `openai/gpt-4o-mini`) |
| `EMBEDDING_MODEL` | No | Embedding model (default: `all-MiniLM-L6-v2`) |
| `TOP_K_RESULTS` | No | Number of retrieval results (default: `10`) |

### Running with Docker

```bash
docker build -t astraeus .
docker run -p 8501:8501 --env-file .env astraeus
```

## Usage

### Web Dashboard

```bash
streamlit run app.py
```

### Command Line Interface

```bash
# Basic research query
python cli.py "How does RAG reduce LLM hallucinations?"

# Save report to file
python cli.py "quantum computing applications" --output report.md

# Web-only retrieval with JSON output
python cli.py "latest transformer architectures" --mode web --json

# List available agents
python cli.py --list-agents
```

### Running Tests

```bash
pytest tests/ -v
```

**Workflow:**
1. Enter a research query in the top navigation bar
2. (Optional) Upload PDF documents for RAG indexing
3. Click **Launch** to start the 6-agent pipeline
4. Watch the live pipeline visualization as each agent processes
5. Review the generated report with citations, confidence scores, and insights
6. Download the markdown report or explore the analytics panels

## Agent Architecture

| # | Agent | Role | Key Capabilities |
|---|-------|------|-----------------|
| 1 | **Research Coordinator** | Master orchestrator | Query analysis, expansion, routing hints |
| 2 | **Contextual Retriever** | Evidence collector | Vector retrieval + web search, reranking, chunk assembly |
| 3 | **Critical Analysis** | Evidence analyzer | Claim extraction, contradiction detection, evidence chains |
| 4 | **Fact-Checker** | Claim verifier | Source credibility scoring, support-count validation |
| 5 | **Insight Generator** | Pattern recognizer | Theme clustering, gap identification, hypothesis creation |
| 6 | **Report Builder** | Final synthesis | Executive summary, key findings, citations, markdown output |

See [AGENTS.md](AGENTS.md) for detailed agent documentation and [ARCHITECTURE.md](ARCHITECTURE.md) for system design.

## Dashboard Sections

- **Top Navigation Bar** - Query input, launch/reset controls, advanced options, live summary cards
- **Agent Pipeline Visualization** - Horizontal 6-card agent lane with animated state transitions
- **Overall Progress Tracker** - Segmented progress strip with complete/total count
- **Token Usage Dashboard** - Input/output/total tokens, per-agent cost and call count
- **RAG Visualization Panel** - Embedding space view, retrieval waterfall, claims and evidence
- **Results Section** - Pipeline metrics, fact-check totals, themes, contradiction-aware reporting
- **Analytics and Insights** - Theme strength, verification distribution, evidence quality
- **Cost Optimization Panel** - Most expensive agent, average cost per call, model-level awareness
- **Export Options** - Download report as Markdown

## Testing

```bash
pytest tests/ -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.

Built as a hackathon submission for the AI Engineering Accelerator, Cohort 4.
