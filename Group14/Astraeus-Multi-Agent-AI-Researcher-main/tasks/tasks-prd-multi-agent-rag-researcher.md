# Task List: Multi-Agent AI Deep Researcher

Generated from **prd-multi-agent-rag-researcher.md** using the generate-tasks framework.  
Target: hackathon-ready app with 6-agent pipeline, 1 vector DB, Streamlit Visual Design System, and key RAG visualizations.

---

## Relevant Files

- `app.py` – Streamlit entry point; top nav (query input, Launch), main pipeline section, and layout orchestration.
- `requirements.txt` – Python dependencies (streamlit, chromadb or qdrant-client, sentence-transformers or openai, langchain or minimal RAG helpers).
- `config.py` – Configuration for vector DB path, embedding model name, and app settings.
- `config.test.py` – Unit tests for config loading and defaults.
- `pipeline/orchestrator.py` – Sequential 6-agent pipeline; triggers agents in order and passes context; updates pipeline state for UI.
- `pipeline/orchestrator.test.py` – Unit tests for pipeline order and state transitions.
- `agents/coordinator.py` – Research Coordinator agent: query analysis, query expansion (multi-query), routing decision for Retriever.
- `agents/retriever.py` – Contextual Retriever agent: single vector DB search, optional hybrid (semantic + keyword) and multi-query retrieval; returns ranked chunks.
- `agents/critical_analysis.py` – Critical Analysis agent: claim extraction, contradiction detection, evidence chains from retrieved docs.
- `agents/fact_checker.py` – Fact-Checker agent: source credibility, cross-check claims.
- `agents/insight_generator.py` – Insight Generation agent: clustering findings, themes, gaps, optional hypothesis generation.
- `agents/report_builder.py` – Report Builder agent: assembles final report with citations from pipeline outputs.
- `rag/vector_store.py` – Abstraction over one local vector DB (Chroma or Qdrant); init, index, query, optional metadata filters.
- `rag/vector_store.test.py` – Unit tests for index and query behavior.
- `rag/embeddings.py` – Single embedding model wrapper (e.g. OpenAI Ada or sentence-transformers); embed query and documents.
- `rag/retrieval.py` – Retrieval logic: multi-query expansion, hybrid search, optional re-ranking or parent-document retrieval.
- `rag/retrieval.test.py` – Unit tests for retrieval pipeline (mocked vector store).
- `ui/components.py` – Reusable Streamlit components: agent card (4 states), inter-agent arrow, pipeline progress bar.
- `ui/styles.py` or `ui/custom.css` – Custom CSS for 4-state card styles, colors, animations (marching ants, glow pulse, progress shimmer).
- `ui/embedding_viewer.py` – Embedding-space viewer: query point + retrieved doc points (2D); click for snippet.
- `ui/retrieval_waterfall.py` – Retrieval waterfall: stages from query → candidates → re-rank → final chunks.
- `ui/source_or_claims.py` – One of: source-routing bar (which DB/source contributed) or claim/evidence list with strength.
- `tasks/prd-multi-agent-rag-researcher.md` – PRD reference (create if missing).

### Notes

- Unit tests can live alongside the code (e.g. `pipeline/orchestrator.py` and `pipeline/orchestrator.test.py`) or in a `tests/` directory; adjust paths in your test runner.
- Run tests with your project’s test runner (e.g. `pytest` or `python -m pytest`). If using Jest (e.g. for a future front-end), use `npx jest [path]` per your setup.

---

## Tasks

- [ ] 1.0 **Project setup and vector DB integration**
  - [ ] 1.1 Create project structure: `app.py`, `config.py`, `requirements.txt`, and folders `pipeline/`, `agents/`, `rag/`, `ui/`.
  - [ ] 1.2 Add dependencies to `requirements.txt`: Streamlit, one vector DB client (Chroma or Qdrant), one embedding library (OpenAI or sentence-transformers), and any RAG/orchestration helpers.
  - [ ] 1.3 Implement `config.py` for vector DB path/connection, embedding model name, and any API keys (e.g. from env); keep one embedding model for v1.
  - [ ] 1.4 Implement `rag/vector_store.py`: connect to one local vector DB (Chroma or Qdrant), support index (documents + metadata) and query (return ranked chunks with optional metadata filters).
  - [ ] 1.5 Implement `rag/embeddings.py`: single embedding model wrapper; embed text(s) and return vectors; use config for model choice.
  - [ ] 1.6 Add a minimal demo corpus or indexing script so the vector store has documents for the demo flow (or document how to load sample data).

- [ ] 2.0 **Research pipeline orchestration and agent logic**
  - [ ] 2.1 Implement `pipeline/orchestrator.py`: sequential pipeline that runs 6 agents in order (Coordinator → Retriever → Critical Analysis → Fact-Checker → Insight Generator → Report Builder); pass context (query, retrieved docs, intermediate outputs) between agents; expose pipeline state (which agent is running, progress) for the UI.
  - [ ] 2.2 Implement Research Coordinator agent: accept user query; perform query expansion (e.g. 3–5 variants for multi-query RAG); output expanded queries and routing hint for Retriever (single DB for v1).
  - [ ] 2.3 Implement Contextual Retriever agent: take expanded queries; call vector store with optional hybrid (semantic + keyword) and multi-query merge; optional re-ranking or parent-document step; return ranked chunks and metadata for visualizations.
  - [ ] 2.4 Implement Critical Analysis agent: from retrieved chunks, extract claims; detect contradictions (e.g. by similarity + opposite sentiment); build simple evidence chains; output structured claims and flags.
  - [ ] 2.5 Implement Fact-Checker agent: use Critical Analysis output; assess source credibility and cross-check key claims; output fact-check notes.
  - [ ] 2.6 Implement Insight Generator agent: cluster findings, identify themes and gaps; optionally generate hypotheses; output themes, gaps, and summary.
  - [ ] 2.7 Implement Report Builder agent: assemble final report from all agent outputs; include citations linking claims to source chunks; output markdown or structured report.

- [ ] 3.0 **Streamlit UI and visual design system**
  - [ ] 3.1 Build top navigation: app title “Multi-Agent AI Deep Researcher”, tagline “6 Agents · RAG-Powered · Autonomous Research Pipeline”, research-query input, Launch button, and placeholders for Settings and Metrics.
  - [ ] 3.2 Implement main pipeline section: “Research Pipeline” heading; horizontal row of 6 agent cards (Research Coordinator, Contextual Retriever, Critical Analysis, Fact-Checker, Insight Generator, Report Builder) with icons and subtitles per design system.
  - [ ] 3.3 Implement agent card component (280×340px, 16px radius, 4 zones: Header, Status, Activity, Output) with 4 states: Not Started (dark, muted), Waiting (amber, dashed border), Working (blue, glow, progress), Complete (green, checkmark); use `st.empty()` or similar for dynamic updates.
  - [ ] 3.4 Add custom CSS for state colors, borders, and animations (marching ants for Waiting, glow pulse for Working, completion flash/bounce for Complete); include animation timing per design system.
  - [ ] 3.5 Implement inter-agent arrows between cards: Inactive (gray dashed), Data flowing (blue, animated when previous complete and current working), Complete (green, subtle pulse).
  - [ ] 3.6 Implement overall pipeline progress bar: segmented (one segment per agent), segment color by agent state; show total elapsed, est. remaining, “Active: [agent]”, “Next: [agent]”.
  - [ ] 3.7 Wire pipeline orchestrator to UI: on Launch, run pipeline and update each agent card state and progress bar in sequence (Not Started → Waiting → Working → Complete).

- [ ] 4.0 **RAG visualizations**
  - [ ] 4.1 Implement embedding-space viewer: reduce query and retrieved-doc embeddings to 2D (e.g. PCA or t-SNE); plot query as distinct point (e.g. red), docs as others (e.g. blue); color or size by relevance; click doc to show snippet in a panel or modal.
  - [ ] 4.2 Implement retrieval waterfall: show stages (e.g. Query → Dense retrieval → Re-rank → Final chunks) with counts or scores per stage; vertical or horizontal layout; use data from Retriever agent output.
  - [ ] 4.3 Implement one of: (a) source-routing bar showing proportion of results by source/metadata (e.g. doc type), or (b) claim/evidence list with strength indicator, using Critical Analysis and Fact-Checker outputs.
  - [ ] 4.4 Place visualizations in the Streamlit layout so they are visible during or after the pipeline run (e.g. below pipeline section or in expanders).

- [ ] 5.0 **End-to-end flow and report output**
  - [ ] 5.1 Connect end-to-end: user enters query → Launch → pipeline runs all 6 agents → agent cards and progress bar update → final report and citations displayed.
  - [ ] 5.2 Add report display area: render Report Builder output (markdown or structured) with clickable or visible citations; ensure at least one demo query completes in under a defined time (e.g. 2–3 minutes) for success metrics.
  - [ ] 5.3 Verify success criteria: all 6 agents produce visible output; cards progress through the 4-state system; pipeline progress bar and arrows behave per design system; embedding viewer and retrieval waterfall render correctly for the demo query.
  - [ ] 5.4 Add minimal error handling and loading states (e.g. pipeline failure shows message; retry or reset option).

---

## Interaction Model

This task list was generated in one pass. If you prefer to adjust the high-level tasks first, revise the **1.0–5.0** parent tasks, then regenerate or edit the sub-tasks accordingly.

## Target Audience

The task list is written for a **junior developer** implementing the feature from the PRD.
