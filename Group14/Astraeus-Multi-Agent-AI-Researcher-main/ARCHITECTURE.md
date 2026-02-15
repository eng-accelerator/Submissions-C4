# System Architecture

## High-Level Design

Astraeus follows a pipeline architecture where 6 specialized agents execute sequentially, each transforming a shared context dictionary.

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Streamlit Dashboard (app.py)                           │
│  - Query input, document upload, pipeline controls      │
│  - Live visualization of agent states                   │
│  - Token/cost tracking, analytics panels                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Pipeline Orchestrator (pipeline/)                       │
│  - Sequential agent execution with shared context       │
│  - State machine: pending → working → complete/error    │
│  - Per-agent telemetry (tokens, cost, latency)          │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │ Agents  │   │ RAG/     │   │ LLM      │
   │ (6)     │   │ Vector   │   │ Gateway   │
   │         │   │ Store    │   │ (OpenRouter)│
   └─────────┘   └──────────┘   └──────────┘
```

## Directory Structure

```
├── app.py                 # Streamlit entry point
├── config.py              # Central configuration and agent definitions
├── agents/                # Agent implementations
│   ├── coordinator.py     # Query analysis and expansion
│   ├── retriever.py       # Multi-source evidence collection
│   ├── critical_analysis.py # Claim extraction and contradiction detection
│   ├── fact_checker.py    # Source credibility and claim verification
│   ├── insight_generator.py # Theme clustering and gap analysis
│   ├── report_builder.py  # Final report synthesis
│   └── report_chat.py     # Interactive report Q&A (optional)
├── pipeline/              # Orchestration logic
├── rag/                   # Vector store and retrieval
│   └── vector_store.py    # Embedding, indexing, and similarity search
├── llm/                   # LLM client wrappers
├── ui/                    # Streamlit UI components and CSS
│   ├── styles.py          # CSS entry point (imports sub-modules)
│   ├── styles_base.py     # Global theme, layout, responsive
│   ├── styles_components.py # Agent cards, badges, robots
│   ├── styles_pipeline.py # Pipeline progress, arrows, timeline
│   └── styles_animations.py # All @keyframes definitions
├── tasks/                 # Task/PRD documentation
├── tests/                 # Test suite
└── data/                  # Vector store persistence
```

## Key Design Decisions

### Sequential Pipeline over Parallel Agents
Agents run sequentially because each stage depends on the previous output. The Retriever needs the Coordinator's expanded queries; Critical Analysis needs the Retriever's chunks; and so on. This makes the data flow explicit and debuggable.

### Shared Context Dictionary
All agents read from and write to a single Python dictionary. This avoids complex message passing while keeping the interface simple. Each agent has a clear contract: required input keys and output keys it adds.

### Local Vector Store
The MVP uses a NumPy-based vector store with JSON persistence rather than an external database. This keeps deployment simple (no Docker dependency for the DB) while the architecture supports swapping in Chroma, Pinecone, or Weaviate via the RAG module interface.

### OpenRouter as LLM Gateway
Using OpenRouter allows switching between Claude, GPT-4, and other models by changing a single environment variable. The LLM module wraps this with token counting and cost tracking.

### CSS Module Architecture
The UI styling is split across 5 files (base, components, pipeline, animations) with a single entry point (`styles.py`) that assembles them. Each file stays under 500 lines, making the CSS maintainable while producing identical output to a monolithic approach.

## Data Flow

1. **User submits query** via Streamlit sidebar
2. **Documents uploaded** (optional) are chunked and embedded into the vector store
3. **Pipeline starts**: Coordinator analyzes query and produces expanded variants
4. **Retriever** searches vector store + optional web search, fuses results
5. **Critical Analysis** extracts claims and detects contradictions
6. **Fact-Checker** verifies claims against source credibility tiers
7. **Insight Generator** clusters themes and identifies knowledge gaps
8. **Report Builder** synthesizes everything into a markdown report
9. **Dashboard updates** in real-time as each agent completes

## Extensibility

- **New agents**: Add a module to `agents/`, register in `config.py`
- **New vector DBs**: Implement the interface in `rag/vector_store.py`
- **New LLM providers**: Add to the OpenRouter model list or extend `llm/`
- **New UI panels**: Add Streamlit components in `ui/`
