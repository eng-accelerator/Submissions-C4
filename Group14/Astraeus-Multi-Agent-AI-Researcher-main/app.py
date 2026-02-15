"""
Astraeus — Multi-Agent AI Deep Researcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Streamlit Application · 6 Agents · RAG-Powered

Run with:
    streamlit run app.py
"""

import streamlit as st
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from pipeline.orchestrator import (
    create_pipeline_state, run_pipeline, PipelineState, AGENT_REGISTRY,
)
from ui.styles import get_custom_css
from ui.components import render_pipeline_cards, render_pipeline_progress, render_metric_card
from ui.embedding_viewer import render_embedding_viewer
from ui.retrieval_waterfall import render_retrieval_waterfall
from ui.source_or_claims import render_claims_evidence
from ui.token_cost_viewer import render_token_cost_viewer
from rag.vector_store import get_collection_count
from rag.document_ingestion import index_uploaded_files
from llm import set_tracking_callback, set_current_agent, clear_tracking
from ui.chat_widget import render_chat_widget

# ══════════════════════════════════════════════════════════════════════
# Page config
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# Session state initialization
# ══════════════════════════════════════════════════════════════════════
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = create_pipeline_state()
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False
if "corpus_loaded" not in st.session_state:
    st.session_state.corpus_loaded = False
if "retrieval_mode" not in st.session_state:
    st.session_state.retrieval_mode = "hybrid"
if "vector_scope" not in st.session_state:
    st.session_state.vector_scope = "all"
if "upload_feedback" not in st.session_state:
    st.session_state.upload_feedback = {}
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


def _summarize_token_tracking(by_agent: dict) -> dict:
    """Aggregate per-agent token/cost data into pipeline totals."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "llm_calls": 0,
    }
    most_expensive = None
    for item in by_agent.values():
        totals["input_tokens"] += int(item.get("input_tokens", 0))
        totals["output_tokens"] += int(item.get("output_tokens", 0))
        totals["total_tokens"] += int(item.get("total_tokens", 0))
        totals["cost_usd"] += float(item.get("cost_usd", 0.0))
        totals["llm_calls"] += int(item.get("llm_calls", 0))
        if most_expensive is None or item.get("cost_usd", 0.0) > most_expensive.get("cost_usd", 0.0):
            most_expensive = item
    totals["cost_usd"] = round(totals["cost_usd"], 6)
    return {
        "by_agent": by_agent,
        "totals": totals,
        "most_expensive_agent": most_expensive or {},
    }

# ══════════════════════════════════════════════════════════════════════
# Load demo corpus on first run
# ══════════════════════════════════════════════════════════════════════
if not st.session_state.corpus_loaded:
    with st.spinner("Loading demo corpus into vector store..."):
        try:
            from data.demo_corpus import load_demo_corpus
            doc_count = load_demo_corpus()
            st.session_state.corpus_loaded = True
            st.session_state.doc_count = doc_count
        except Exception as e:
            st.error(f"Failed to load demo corpus: {e}")
            st.session_state.corpus_loaded = True  # don't retry
            st.session_state.doc_count = 0


# ══════════════════════════════════════════════════════════════════════
# TOP NAVIGATION
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="top-bar">
    <div class="app-title">🔬 {config.APP_TITLE}</div>
    <div class="app-tagline">AI Research Assistant</div>
</div>
""", unsafe_allow_html=True)

# ── Query input row ───────────────────────────────────────────────────
col_input, col_btn, col_reset = st.columns([6, 1.2, 1])

with col_input:
    query = st.text_input(
        "Research Query",
        placeholder="e.g., How does RAG reduce LLM hallucinations?",
        label_visibility="collapsed",
        key="research_query",
    )

with col_btn:
    launch = st.button("🚀 Launch Research", use_container_width=True, type="primary")

with col_reset:
    reset = st.button("🔄 Reset", use_container_width=True)

if reset:
    st.session_state.pipeline_state = create_pipeline_state()
    st.session_state.pipeline_ran = False
    st.session_state.upload_feedback = {}
    st.session_state.chat_messages = []
    st.rerun()

# ── Upload panel (primary flow, compact) ───────────────────────────────
st.markdown("#### 📤 Research with your documents")
up_col1, up_col2 = st.columns([5.3, 1.7])
with up_col1:
    uploaded_files = st.file_uploader(
        "Include your files (optional)",
        type=["txt", "md", "csv", "json", "log", "pdf"],
        accept_multiple_files=True,
        key="upload_documents",
        label_visibility="collapsed",
    )
with up_col2:
    add_files = st.button("Add files", use_container_width=True)

if add_files:
    if not uploaded_files:
        st.warning("Select at least one file first.")
    else:
        with st.spinner("Parsing and embedding uploaded documents..."):
            result = index_uploaded_files(uploaded_files)
            total_docs = get_collection_count()
            st.session_state.doc_count = total_docs
            st.session_state.upload_feedback = {
                "result": result,
                "total_docs": total_docs,
            }

feedback = st.session_state.get("upload_feedback", {})
status_text = "Using web + indexed docs."
status_level = "caption"
if feedback:
    result = feedback.get("result", {})
    total_docs = feedback.get("total_docs", st.session_state.get("doc_count", 0))
    files_ok = result.get("files_processed", 0)
    files_failed = result.get("files_failed", 0)
    chunks_indexed = result.get("chunks_indexed", 0)
    if files_ok > 0:
        status_text = (
            f"✅ Ready: {files_ok} file(s), {chunks_indexed} chunks indexed, "
            f"{total_docs} total indexed docs. Included in next launch."
        )
        status_level = "success"
    elif files_failed > 0:
        status_text = "⚠️ No files were indexed successfully."
        status_level = "warning"
    if files_failed > 0:
        with st.expander("Upload errors"):
            for err in result.get("errors", []):
                st.write(f"- {err}")
elif uploaded_files:
    status_text = f"📎 {len(uploaded_files)} file(s) selected. Click Add files to include them in research."

if status_level == "success":
    st.success(status_text)
elif status_level == "warning":
    st.warning(status_text)
else:
    st.caption(status_text)

# ── Settings & Metrics bar ────────────────────────────────────────────
with st.expander("⚙️ Advanced options", expanded=False):
    from llm import is_available as llm_available
    s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
    with s_col1:
        render_metric_card("Documents Indexed", str(st.session_state.get("doc_count", 0)), "📚")
    with s_col2:
        render_metric_card("Embedding Model", config.EMBEDDING_MODEL, "🧠")
    with s_col3:
        llm_label = f"OpenRouter · {config.LLM_MODEL}" if llm_available() else "Not configured"
        render_metric_card("LLM", llm_label[:20] + "…" if len(llm_label) > 20 else llm_label, "🤖")
    with s_col4:
        render_metric_card("Top-K Results", str(config.TOP_K_RESULTS), "🎯")
    with s_col5:
        render_metric_card("Query Expansions", str(config.MAX_QUERY_EXPANSIONS), "🔀")

    st.markdown("#### 🔎 Retrieval Settings")
    mode_col, scope_col = st.columns(2)
    with mode_col:
        selected_mode = st.selectbox(
            "Search Mode",
            options=[
                ("Web + Vector DB", "hybrid"),
                ("Only Vector DB", "vector_only"),
                ("Only Web Search", "web_only"),
            ],
            index=0 if st.session_state.retrieval_mode == "hybrid" else 1 if st.session_state.retrieval_mode == "vector_only" else 2,
            format_func=lambda x: x[0],
            help="Choose whether retrieval uses indexed docs, web search, or both.",
        )
        st.session_state.retrieval_mode = selected_mode[1]

    with scope_col:
        selected_scope = st.selectbox(
            "Search In",
            options=[
                ("All Indexed Docs (demo + uploads)", "all"),
                ("My uploaded files only", "uploaded_only"),
            ],
            index=0 if st.session_state.vector_scope == "all" else 1,
            format_func=lambda x: x[0],
            help="When vector retrieval is enabled, pick which indexed content is searched.",
        )
        st.session_state.vector_scope = selected_scope[1]

# ══════════════════════════════════════════════════════════════════════
# RESEARCH PIPELINE SECTION
# ══════════════════════════════════════════════════════════════════════
st.markdown("### 🔬 Research Pipeline")

pipeline_state = st.session_state.pipeline_state
show_pipeline = st.session_state.pipeline_ran or pipeline_state.is_running

progress_placeholder = None
cards_placeholder = None

if show_pipeline:
    # ── Live-update placeholders (replaced in-place during pipeline run) ──
    progress_placeholder = st.empty()
    cards_placeholder = st.empty()

    # Render current state (static when idle, will be replaced during run)
    with progress_placeholder.container():
        render_pipeline_progress(pipeline_state)
    with cards_placeholder.container():
        render_pipeline_cards(pipeline_state)
else:
    st.info("Pipeline ready • 6 agents • Click Launch Research to begin.")

# ══════════════════════════════════════════════════════════════════════
# LAUNCH PIPELINE — step-by-step with live UI updates
# ══════════════════════════════════════════════════════════════════════
if launch and query.strip():
    # Fresh pipeline state
    pipeline_state = create_pipeline_state()
    st.session_state.pipeline_state = pipeline_state
    st.session_state.pipeline_ran = False
    token_by_agent = {
        a["id"]: {
            "agent_id": a["id"],
            "name": a["name"],
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "llm_calls": 0,
            "elapsed_seconds": 0.0,
        }
        for a in AGENT_REGISTRY
    }

    def _on_llm_usage(event: dict):
        agent_id = event.get("agent_id", "unknown")
        if agent_id not in token_by_agent:
            token_by_agent[agent_id] = {
                "agent_id": agent_id,
                "name": agent_id.replace("_", " ").title(),
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
                "llm_calls": 0,
                "elapsed_seconds": 0.0,
            }
        item = token_by_agent[agent_id]
        item["input_tokens"] += int(event.get("input_tokens", 0))
        item["output_tokens"] += int(event.get("output_tokens", 0))
        item["total_tokens"] += int(event.get("total_tokens", 0))
        item["cost_usd"] += float(event.get("cost_usd", 0.0))
        item["llm_calls"] += 1

    if config.TOKEN_TRACKING_ENABLED:
        set_tracking_callback(_on_llm_usage)

    # Create placeholders on-demand if pipeline was hidden pre-launch
    if progress_placeholder is None or cards_placeholder is None:
        progress_placeholder = st.empty()
        cards_placeholder = st.empty()

    # Helper to repaint both placeholders
    def _repaint():
        with progress_placeholder.container():
            render_pipeline_progress(pipeline_state)
        with cards_placeholder.container():
            render_pipeline_cards(pipeline_state)

    # ── Run the single orchestrator path ──────────────────────────────
    initial_context = {
        "retrieval_mode": st.session_state.get("retrieval_mode", "hybrid"),
        "vector_scope": st.session_state.get("vector_scope", "all"),
    }
    _repaint()

    def _on_state_change(updated_state: PipelineState):
        with progress_placeholder.container():
            render_pipeline_progress(updated_state)
        with cards_placeholder.container():
            render_pipeline_cards(updated_state)

    try:
        pipeline_state = run_pipeline(
            query=query.strip(),
            state=pipeline_state,
            on_state_change=_on_state_change,
            initial_context=initial_context,
            before_agent_run=(set_current_agent if config.TOKEN_TRACKING_ENABLED else None),
            after_agent_run=((lambda _agent_id: set_current_agent(None)) if config.TOKEN_TRACKING_ENABLED else None),
        )
    finally:
        if config.TOKEN_TRACKING_ENABLED:
            clear_tracking()

    for idx, agent_def in enumerate(AGENT_REGISTRY):
        token_by_agent[agent_def["id"]]["elapsed_seconds"] = pipeline_state.agents[idx].elapsed_seconds
        token_by_agent[agent_def["id"]]["cost_usd"] = round(token_by_agent[agent_def["id"]]["cost_usd"], 6)
        agent = pipeline_state.agents[idx]
        agent_tokens = token_by_agent[agent_def["id"]].get("total_tokens", 0)
        agent_cost = token_by_agent[agent_def["id"]].get("cost_usd", 0.0)
        if config.TOKEN_TRACKING_ENABLED and agent_tokens > 0 and "Tokens:" not in agent.output_summary:
            agent.output_summary += f" | Tokens: {agent_tokens:,} | Cost: ${agent_cost:.4f}"
    pipeline_state.context["token_tracking"] = _summarize_token_tracking(token_by_agent)

    st.session_state.pipeline_state = pipeline_state
    st.session_state.pipeline_ran = True
    st.session_state.chat_messages = []   # fresh chat for new research

    # Final rerun so downstream sections (report, viz) render
    st.rerun()

elif launch and not query.strip():
    st.warning("Please enter a research query before launching the pipeline.")

# ══════════════════════════════════════════════════════════════════════
# POST-PIPELINE: Results & Visualizations
# ══════════════════════════════════════════════════════════════════════
if st.session_state.pipeline_ran and pipeline_state.is_complete:
    context = pipeline_state.context

    # ── Summary metrics ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Pipeline Results")

    token_totals = context.get("token_tracking", {}).get("totals", {})
    metric_cols = st.columns(6 if config.TOKEN_TRACKING_ENABLED else 5)
    m1, m2, m3, m4, m5 = metric_cols[:5]
    with m1:
        render_metric_card(
            "Total Time",
            f"{pipeline_state.total_elapsed:.1f}s",
            "⏱️",
        )
    with m2:
        render_metric_card(
            "Chunks Retrieved",
            str(context.get("retrieval_metadata", {}).get("total_chunks", 0)),
            "📄",
        )
    with m3:
        render_metric_card(
            "Claims Extracted",
            str(len(context.get("claims", []))),
            "📝",
        )
    with m4:
        verified = sum(1 for r in context.get("fact_check_results", []) if r["verdict"] == "verified")
        render_metric_card("Verified Claims", str(verified), "✅")
    with m5:
        render_metric_card(
            "Themes Found",
            str(len(context.get("themes", []))),
            "💡",
        )
    if config.TOKEN_TRACKING_ENABLED:
        m6 = metric_cols[5]
        with m6:
            render_metric_card(
                "LLM Cost",
                f"${token_totals.get('cost_usd', 0.0):.4f}",
                "💵",
            )

    # ── RAG Visualizations ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎨 RAG Visualizations")

    tab_labels = ["🗺️ Embedding Space", "🏗️ Retrieval Waterfall", "✅ Claims & Evidence", "💬 Report Chat"]
    if config.TOKEN_TRACKING_ENABLED:
        tab_labels.append("📊 Token & Cost")
    tabs = st.tabs(tab_labels)
    viz_tab1, viz_tab2, viz_tab3, chat_tab = tabs[:4]

    with viz_tab1:
        render_embedding_viewer(context)

    with viz_tab2:
        render_retrieval_waterfall(context)

    with viz_tab3:
        render_claims_evidence(context)

    with chat_tab:
        render_chat_widget(context)

    if config.TOKEN_TRACKING_ENABLED:
        with tabs[4]:
            render_token_cost_viewer(context)

    # ── Final Report ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📄 Research Report")

    report = context.get("report_markdown", "")
    if report:
        st.markdown(
            '<div class="report-container">',
            unsafe_allow_html=True,
        )
        st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="📥 Download Report (Markdown)",
            data=report,
            file_name="research_report.md",
            mime="text/markdown",
        )
    else:
        st.info("No report generated. Try running the pipeline again.")

# ── Pipeline error display ────────────────────────────────────────────
if pipeline_state.has_error:
    st.markdown("---")
    st.error("⚠️ Pipeline encountered an error")
    error_info = pipeline_state.context.get("pipeline_error", {})
    if error_info:
        st.markdown(f"**Agent:** {error_info.get('agent', 'Unknown')}")
        st.markdown(f"**Error:** {error_info.get('error', 'Unknown error')}")
        if config.DEBUG or config.SHOW_TRACEBACK:
            with st.expander("Traceback"):
                st.code(error_info.get("traceback", ""), language="python")
        else:
            st.caption("Detailed traceback hidden outside debug mode.")

    if st.button("🔄 Retry Pipeline"):
        st.session_state.pipeline_state = create_pipeline_state()
        st.session_state.pipeline_ran = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    f'<div style="text-align:center;color:#64748b;font-size:0.8rem;padding:16px;">'
    f'🔬 {config.APP_TITLE} | {config.APP_TAGLINE}'
    '</div>',
    unsafe_allow_html=True,
)
