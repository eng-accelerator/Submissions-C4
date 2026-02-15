"""
app.py
======
Streamlit UI for the Multi-Agent AI Deep Researcher.

Run with: streamlit run app.py

Features:
    - Clean, professional research interface
    - Real-time agent progress tracking
    - Expandable sections for each part of the report
    - Confidence-coded findings (green/yellow/red)
    - PDF export and download
    - Research history in sidebar
    - Model selection and settings
"""

from __future__ import annotations

import time
import logging
import streamlit as st
from datetime import datetime

from config import settings, AVAILABLE_MODELS
from utils.llm_client import LLMClient
from utils.callbacks import ProgressTracker
from agents.report_agent import ReportResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helper Functions (defined early so Streamlit can find them)
# ─────────────────────────────────────────────

def _build_markdown_report(report: dict, sources: list) -> str:
    """Build a Markdown version of the report for download."""
    lines = [
        f"# {report.get('title', 'Research Report')}",
        f"*Generated: {report.get('generated_at', datetime.now().isoformat())}*",
        f"*Quality Score: {report.get('quality_score', 0)}/100*",
        "",
        "## Executive Summary",
        report.get("executive_summary", ""),
        "",
        "## Key Findings",
    ]

    for i, f in enumerate(report.get("key_findings", []), 1):
        confidence = f.get("confidence", "N/A")
        lines.append(f"{i}. **[{confidence}%]** {f.get('finding', '')}")

    lines.extend([
        "",
        "## Contradictions & Gaps",
        report.get("contradictions_and_gaps", ""),
        "",
        "## Insights & Trends",
        report.get("insights_and_trends", ""),
        "",
        "## Source Reliability",
        report.get("source_reliability", ""),
        "",
        "## Methodology",
        report.get("methodology_note", ""),
        "",
        "## Sources",
    ])

    for i, s in enumerate(sources, 1):
        lines.append(f"{i}. [{s.get('title', 'Unknown')}]({s.get('url', '')})")

    return "\n".join(lines)

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS for professional styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: #e94560;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #a8a8b3;
        font-size: 1rem;
    }

    /* Finding confidence badges */
    .confidence-high {
        background-color: #27ae60;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confidence-medium {
        background-color: #f39c12;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confidence-low {
        background-color: #e74c3c;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }

    /* Quality score display */
    .quality-score-box {
        text-align: center;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .quality-high { background: linear-gradient(135deg, #27ae6020, #2ecc7120); border: 2px solid #27ae60; }
    .quality-medium { background: linear-gradient(135deg, #f39c1220, #e67e2220); border: 2px solid #f39c12; }
    .quality-low { background: linear-gradient(135deg, #e74c3c20, #c0392b20); border: 2px solid #e74c3c; }

    /* Agent status indicators */
    .agent-running { color: #3498db; }
    .agent-complete { color: #27ae60; }
    .agent-error { color: #e74c3c; }

    /* Source cards */
    .source-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        background: #fafafa;
    }

    /* Stat boxes */
    .stMetric { border-radius: 8px; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────
if "research_history" not in st.session_state:
    st.session_state.research_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False


# ─────────────────────────────────────────────
# Sidebar — Settings & History
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Settings")

    # Model selection
    model_display = st.selectbox(
        "LLM Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.values()).index(settings.DEFAULT_MODEL)
        if settings.DEFAULT_MODEL in AVAILABLE_MODELS.values()
        else 0,
        help="Select the LLM model for analysis. Free models have usage limits.",
    )
    selected_model = AVAILABLE_MODELS[model_display]

    # Max iterations
    max_iterations = st.slider(
        "Max Reflection Loops",
        min_value=1,
        max_value=3,
        value=settings.MAX_ITERATIONS,
        help="How many times the system can refine its research if quality is low.",
    )

    # Quality threshold
    quality_threshold = st.slider(
        "Quality Threshold",
        min_value=30,
        max_value=90,
        value=int(settings.QUALITY_THRESHOLD),
        step=5,
        help="Minimum quality score (0-100) to accept the report.",
    )

    st.divider()

    # Research History
    st.markdown("## Research History")
    if st.session_state.research_history:
        for i, entry in enumerate(reversed(st.session_state.research_history)):
            timestamp = entry.get("timestamp", "")
            query = entry.get("query", "")[:50]
            score = entry.get("quality_score", 0)
            with st.expander(f"{query}...", expanded=False):
                st.caption(f"Time: {timestamp}")
                st.caption(f"Quality: {score}/100")
                if st.button(f"Load", key=f"load_{i}"):
                    st.session_state.current_result = entry.get("result")
                    st.rerun()
    else:
        st.caption("No research sessions yet.")

    st.divider()

    # API Key Status
    st.markdown("## API Status")
    openrouter_ok = bool(settings.OPENROUTER_API_KEY)
    tavily_ok = bool(settings.TAVILY_API_KEY)
    st.markdown(f"{'✅' if openrouter_ok else '❌'} OpenRouter API Key")
    st.markdown(f"{'✅' if tavily_ok else '❌'} Tavily API Key")
    if not (openrouter_ok and tavily_ok):
        st.warning("Missing API keys! Copy `.env.example` to `.env` and add your keys.")

    st.divider()

    # ── Usage Stats Widget ─────────────────────────────────
    st.markdown("## Usage Stats")
    _current = st.session_state.get("current_result")
    if _current and _current.get("usage_stats"):
        _usage = _current["usage_stats"]
        _by_agent = _usage.get("by_agent", {})
        _total_tok = _usage.get("total_tokens", 0)
        _total_calls = _usage.get("total_calls", 0)
        _tavily_calls = _usage.get("tavily_calls", 0)

        # Summary metrics
        st.metric("Total LLM Tokens", f"{_total_tok:,}")
        _cols = st.columns(2)
        with _cols[0]:
            st.metric("LLM Calls", _total_calls)
        with _cols[1]:
            st.metric("Tavily Searches", _tavily_calls)

        # Per-agent token breakdown
        with st.expander("Token Breakdown by Agent", expanded=True):
            # Agent order for display
            _agent_order = ["Decomposer", "Retriever", "Analyzer", "Fact-Checker", "Insight", "Reporter"]
            for _agent_name in _agent_order:
                if _agent_name in _by_agent:
                    _a = _by_agent[_agent_name]
                    _pct = (_a["total_tokens"] / _total_tok * 100) if _total_tok > 0 else 0
                    st.markdown(
                        f"**{_agent_name}** — "
                        f"`{_a['total_tokens']:,}` tokens "
                        f"({_a['calls']} call{'s' if _a['calls'] != 1 else ''})"
                    )
                    st.progress(min(_pct / 100, 1.0))
            # Any agents not in the predefined order
            for _agent_name, _a in _by_agent.items():
                if _agent_name not in _agent_order:
                    st.markdown(f"**{_agent_name}** — `{_a['total_tokens']:,}` tokens")

        # Sub-queries used
        _sub_queries = _current.get("sub_queries", [])
        if _sub_queries:
            with st.expander(f"Sub-Queries ({len(_sub_queries)})", expanded=True):
                for _i, _sq in enumerate(_sub_queries, 1):
                    st.markdown(f"{_i}. {_sq}")
    else:
        st.caption("Run a research query to see usage stats.")


# ─────────────────────────────────────────────
# Main Content Area
# ─────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>🔬 AI Deep Researcher</h1>
    <p>Multi-Agent Research System — Powered by LangGraph + Tavily + OpenRouter</p>
</div>
""", unsafe_allow_html=True)

# Pre-populate search box when an example topic is clicked
if "_example_query" in st.session_state:
    st.session_state["research_query"] = st.session_state.pop("_example_query")

# Research Input
col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input(
        "What would you like to research?",
        placeholder="e.g., Impact of AI on healthcare costs in 2024",
        label_visibility="collapsed",
        key="research_query",
    )
with col2:
    research_clicked = st.button(
        "🔍 Research",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_researching,
    )

# Example queries
with st.expander("💡 Example Research Topics", expanded=not bool(st.session_state.current_result)):
    example_cols = st.columns(3)
    examples = [
        "Impact of quantum computing on cybersecurity by 2030",
        "Latest breakthroughs in nuclear fusion energy 2024-2025",
        "How is AI changing drug discovery and pharmaceutical R&D?",
        "Global water scarcity crisis: causes, effects, and solutions",
        "Rise of lab-grown meat: environmental and economic impact",
        "Future of remote work: productivity data and trends",
    ]
    for i, example in enumerate(examples):
        col = example_cols[i % 3]
        with col:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state["_example_query"] = example
                st.rerun()

# ─────────────────────────────────────────────
# Research Execution
# ─────────────────────────────────────────────

if research_clicked and query:
    # Validate API keys
    try:
        settings.validate()
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.session_state.is_researching = True
    st.session_state.current_result = None

    # Initialize LLM with selected model
    llm = LLMClient(model=selected_model)

    # Override settings for this run
    settings.QUALITY_THRESHOLD = float(quality_threshold)

    st.divider()
    st.markdown(f"### Researching: *{query}*")

    # Run pipeline inside st.status — the ProgressTracker writes
    # live updates into this container so each agent is visible in real time.
    start_time = time.time()

    with st.status("🔬 Running multi-agent research pipeline...", expanded=True) as status:
        from orchestrator.graph import run_research

        # Show pipeline config
        st.write(f"**Model:** {model_display}")
        st.write(f"**Max iterations:** {max_iterations}")
        st.write(f"**Quality threshold:** {quality_threshold}/100")
        st.divider()

        # Create tracker with live reference to the st.status container
        tracker = ProgressTracker(live_container=status)

        # Execute research — agents write progress into `status` in real-time
        result = run_research(
            query=query,
            llm=llm,
            tracker=tracker,
            max_iterations=max_iterations,
        )

        elapsed = time.time() - start_time

        quality = result.get("quality_score", 0)
        if quality >= quality_threshold:
            status.update(
                label=f"✅ Research complete! Quality: {quality:.0f}/100 ({elapsed:.1f}s)",
                state="complete",
            )
        else:
            status.update(
                label=f"⚠️ Research complete (quality: {quality:.0f}/100). {elapsed:.1f}s",
                state="complete",
            )

    # Store result and add to history
    st.session_state.current_result = result
    st.session_state.is_researching = False

    st.session_state.research_history.append({
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "quality_score": result.get("quality_score", 0),
        "result": result,
    })

    # Rerun so the sidebar picks up usage_stats & sub-queries
    st.rerun()


# ─────────────────────────────────────────────
# Results Display
# ─────────────────────────────────────────────

result = st.session_state.current_result

if result and result.get("report"):
    report = result["report"]
    sources = result.get("sources", [])
    fact_check = result.get("fact_check", {})
    insights = result.get("insights", {})

    st.divider()

    # ── Header Metrics ───────────────────────────────────
    st.markdown(f"## 📄 {report.get('title', 'Research Report')}")

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Sources", len(sources))
    with metric_cols[1]:
        st.metric("Findings", len(report.get("key_findings", [])))
    with metric_cols[2]:
        reliability = fact_check.get("overall_reliability_score", "N/A")
        st.metric("Reliability", f"{reliability}/100")
    with metric_cols[3]:
        quality = report.get("quality_score", 0)
        st.metric("Quality", f"{quality:.0f}/100")

    # ── Quality Score Visual ─────────────────────────────
    quality_class = "quality-high" if quality >= 70 else ("quality-medium" if quality >= 50 else "quality-low")
    breakdown = report.get("quality_breakdown", {})
    breakdown_html = " | ".join(f"{k.title()}: {v}" for k, v in breakdown.items()) if breakdown else ""
    st.markdown(f"""
    <div class="quality-score-box {quality_class}">
        <h2 style="margin:0">Research Quality: {quality:.0f}/100</h2>
        <p style="margin:0.5rem 0 0 0; font-size:0.85rem">{breakdown_html}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Report Tabs ──────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Executive Summary",
        "🔍 Key Findings",
        "⚡ Contradictions & Gaps",
        "💡 Insights & Trends",
        "📊 Sources",
        "📥 Export",
    ])

    # Tab 1: Executive Summary
    with tab1:
        st.markdown(report.get("executive_summary", "No summary available."))

    # Tab 2: Key Findings
    with tab2:
        findings = report.get("key_findings", [])
        if findings:
            for i, f in enumerate(findings, 1):
                confidence = f.get("confidence", 50)
                if isinstance(confidence, (int, float)):
                    if confidence >= 70:
                        badge_class = "confidence-high"
                    elif confidence >= 50:
                        badge_class = "confidence-medium"
                    else:
                        badge_class = "confidence-low"
                    badge = f'<span class="{badge_class}">{confidence}%</span>'
                else:
                    badge = f'<span class="confidence-medium">{confidence}</span>'

                st.markdown(
                    f"**{i}.** {badge} {f.get('finding', '')}",
                    unsafe_allow_html=True,
                )
                sources_count = f.get("sources_count", 0)
                if sources_count:
                    st.caption(f"Supported by {sources_count} source(s)")
                st.divider()
        else:
            st.info("No key findings extracted.")

    # Tab 3: Contradictions & Gaps
    with tab3:
        st.markdown(report.get("contradictions_and_gaps", "No contradictions or gaps identified."))

        # Show fact-check warnings
        warnings = fact_check.get("warnings", [])
        if warnings:
            st.markdown("### ⚠️ Fact-Check Warnings")
            for w in warnings:
                st.warning(w)

    # Tab 4: Insights & Trends
    with tab4:
        st.markdown(report.get("insights_and_trends", "No insights generated."))

        # Show hypotheses detail
        hypotheses = insights.get("hypotheses", [])
        if hypotheses:
            st.markdown("### Hypotheses")
            for h in hypotheses:
                with st.expander(
                    f"{'🟢' if h.get('confidence') == 'high' else '🟡' if h.get('confidence') == 'medium' else '🔴'} "
                    f"{h.get('statement', '')}",
                    expanded=False,
                ):
                    st.markdown(f"**Confidence:** {h.get('confidence', 'unknown')}")
                    st.markdown(f"**Reasoning:** {h.get('reasoning_chain', 'N/A')}")
                    evidence = h.get("supporting_evidence", [])
                    if evidence:
                        st.markdown("**Evidence:**")
                        for e in evidence:
                            st.markdown(f"- {e}")

        # Show trends
        trends = insights.get("trends", [])
        if trends:
            st.markdown("### Trends")
            for t in trends:
                direction_icon = {
                    "increasing": "📈",
                    "decreasing": "📉",
                    "emerging": "🌱",
                    "shifting": "🔄",
                    "stable": "➡️",
                }.get(t.get("direction", ""), "📊")
                st.markdown(f"{direction_icon} **{t.get('description', '')}**")
                st.caption(f"Direction: {t.get('direction', 'unknown')} | Timeframe: {t.get('timeframe', 'unknown')}")

        # Show further questions
        further_q = insights.get("further_questions", [])
        if further_q:
            st.markdown("### 🔮 Suggested Follow-up Questions")
            for q in further_q:
                st.markdown(f"- {q}")

    # Tab 5: Sources
    with tab5:
        if sources:
            # Source type distribution
            type_counts = {}
            for s in sources:
                t = s.get("source_type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1

            st.markdown(f"### Source Distribution ({len(sources)} total)")

            dist_cols = st.columns(len(type_counts) if type_counts else 1)
            for i, (stype, count) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
                with dist_cols[i % len(dist_cols)]:
                    st.metric(stype.title(), count)

            st.divider()

            # Source list
            for i, src in enumerate(sources, 1):
                with st.expander(
                    f"[{src.get('source_type', 'unknown').upper()}] {src.get('title', 'Untitled')}",
                    expanded=False,
                ):
                    st.markdown(f"**URL:** [{src.get('url', '')}]({src.get('url', '')})")
                    st.markdown(f"**Domain:** {src.get('domain', 'unknown')}")
                    st.markdown(f"**Relevance:** {src.get('relevance_score', 0):.2f}")
                    st.markdown(f"**Sub-query:** {src.get('sub_query', 'N/A')}")
                    st.text_area(
                        "Content",
                        src.get("content", "")[:1000],
                        height=150,
                        key=f"source_content_{i}",
                        disabled=True,
                    )
        else:
            st.info("No sources collected.")

    # Tab 6: Export
    with tab6:
        st.markdown("### Export Report")
        st.markdown("Download the research report in your preferred format.")
        st.markdown("")

        # Pre-generate PDF bytes (no rerun needed)
        from utils.pdf_export import generate_pdf_bytes
        try:
            pdf_bytes = generate_pdf_bytes(report, sources)
            pdf_ready = True
        except Exception as e:
            pdf_bytes = None
            pdf_ready = False
            logger.error(f"PDF generation failed: {e}")

        # Pre-generate Markdown content
        md_content = _build_markdown_report(report, sources)

        col_pdf, col_md = st.columns(2)

        with col_pdf:
            st.markdown("#### PDF Report")
            st.caption("Professional formatted document with styled sections and confidence badges.")
            if pdf_ready:
                st.download_button(
                    "📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.error("PDF generation failed. Try the Markdown export instead.")

        with col_md:
            st.markdown("#### Markdown Report")
            st.caption("Plain text format compatible with Notion, GitHub, Obsidian, etc.")
            st.download_button(
                "📝 Download Markdown",
                data=md_content,
                file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # Show methodology
        st.divider()
        st.markdown("### Methodology")
        st.markdown(report.get("methodology_note", ""))

        # Show errors if any
        errors = result.get("errors", [])
        if errors:
            st.markdown("### ⚠️ Pipeline Errors")
            for err in errors:
                st.error(err)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.8rem;'>"
    "Multi-Agent AI Deep Researcher | Built with LangGraph + Tavily + Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
