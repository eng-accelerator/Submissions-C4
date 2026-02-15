"""
Reusable Streamlit components for the visual design system.
Agent cards, inter-agent arrows, pipeline progress bar, and metric cards.
"""

from __future__ import annotations
import html
import streamlit as st
from pipeline.orchestrator import AgentState, AgentStatus, PipelineState
import config


def render_agent_card(agent_status: AgentStatus, agent_config: dict):
    """Render one themed animated agent card."""
    state = agent_status.state.value
    name = _safe_text(agent_config.get("name", agent_status.name))
    subtitle = _safe_text(agent_config.get("subtitle", ""))
    badge_icon = _safe_text(agent_config.get("badge_icon", "🔹"))
    color = _safe_text(agent_config.get("color", "#3b82f6"))
    state_label = {
        "not_started": "Pending",
        "waiting": "Pending",
        "working": "Running",
        "complete": "Complete",
        "error": "Error",
    }.get(state, "Pending")
    progress_pct = {
        "not_started": 8,
        "waiting": 20,
        "working": 62,
        "complete": 100,
        "error": 100,
    }.get(state, 8)
    glow_alpha = 0.42 if state == "working" else 0.26 if state == "complete" else 0.18
    elapsed_label = f"{agent_status.elapsed_seconds:.1f}s" if agent_status.elapsed_seconds > 0 else "0.0s"
    long_descriptions = {
        "coordinator": (
            "Breaks down your research goal, defines intent, and creates structured query paths."
        ),
        "retriever": (
            "Collects evidence from indexed documents and search results, then ranks best matches."
        ),
        "critical_analysis": (
            "Extracts claims, highlights contradictions, and flags logic gaps across sources."
        ),
        "fact_checker": (
            "Cross-validates claims with references, credibility signals, and consistency checks."
        ),
        "insight_generator": (
            "Finds themes, hidden opportunities, and strategic hypotheses from verified findings."
        ),
        "report_builder": (
            "Converts all validated insights into a structured final report with clear citations."
        ),
    }
    long_description = _safe_text(long_descriptions.get(agent_status.agent_id, subtitle))

    if state == "complete" and agent_status.output_summary:
        detailed_metrics = _safe_text(agent_status.output_summary)
    elif state == "working":
        detailed_metrics = _safe_text("Metrics updating live as this stage processes...")
    elif state == "error":
        detailed_metrics = _safe_text(agent_status.error_message or "Error while generating metrics.")
    else:
        detailed_metrics = _safe_text("Awaiting execution metrics.")

    tooltip_title = _safe_text(f"About: {long_description} | Details: {detailed_metrics}")

    card_html = f"""
    <div class="agent-card {state}" style="--agent-color:{color};--agent-glow:rgba(255,255,255,{glow_alpha});">
        <div class="agent-badge agent-info-trigger" tabindex="0" role="button" aria-label="Show agent details" title="{tooltip_title}">
            <span class="agent-badge-icon">{badge_icon}</span>
            <div class="agent-tooltip" role="tooltip">
                <div class="agent-tooltip-title">Agent details</div>
                <div class="agent-tooltip-line"><strong>About:</strong> {long_description}</div>
                <div class="agent-tooltip-line"><strong>Metrics:</strong> {detailed_metrics}</div>
            </div>
        </div>
        <div class="agent-main-hero">
            <div class="robot-stage">
                <div class="robot-halo"></div>
                <div class="robot-hero robot-{agent_status.agent_id}">
                    <div class="robot-antenna"><span class="antenna-tip"></span></div>
                    <div class="robot-head">
                        <div class="robot-eyes"><span></span><span></span></div>
                        <div class="robot-mouth"></div>
                    </div>
                    <div class="robot-body"></div>
                </div>
            </div>
            <div class="agent-name">{name}</div>
            <div class="agent-status-inline status-{state}">
                <span class="status-dot"></span>
                <span>{state_label}</span>
            </div>
            <div class="agent-progress-track">
                <div class="agent-progress-fill state-{state}" style="width:{progress_pct}%;"></div>
            </div>
            <div class="agent-elapsed">Execution: {elapsed_label}</div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def _safe_text(value: object) -> str:
    """Escape dynamic text and filter malformed HTML residue."""
    if value is None:
        return ""
    text = str(value).strip()
    text = text.replace("</div>", "").replace("<div>", "").strip()
    return html.escape(text)


def render_arrow(prev_state: str, current_state: str, next_color: str):
    """Render an inter-agent arrow between two cards."""
    if prev_state == "complete" and current_state == "working":
        arrow_class = "arrow-flowing"
        arrow_char = "→"
    elif prev_state == "complete" and current_state == "complete":
        arrow_class = "arrow-complete"
        arrow_char = "→"
    else:
        arrow_class = "arrow-inactive"
        arrow_char = "→"

    beam_html = '<span class="arrow-beam"></span>' if arrow_class == "arrow-flowing" else ""
    st.markdown(
        (
            '<div class="arrow-container">'
            f'<span class="{arrow_class}" style="--arrow-color:{_safe_text(next_color)};">{arrow_char}</span>'
            f"{beam_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_pipeline_progress(pipeline_state: PipelineState):
    """Render a compact themed segmented progress bar."""
    segments_html = ""
    for idx, agent in enumerate(pipeline_state.agents):
        state = agent.state.value
        cfg = config.AGENTS[idx] if idx < len(config.AGENTS) else {}
        seg_color = _safe_text(cfg.get("color", "#3b82f6"))
        segments_html += (
            f'<div class="progress-segment {state}" style="--segment-color:{seg_color};"></div>'
        )

    completed = sum(1 for a in pipeline_state.agents if a.state == AgentState.COMPLETE)
    total = len(pipeline_state.agents)
    progress_pct = (completed / total * 100) if total > 0 else 0
    active_label = "Running" if pipeline_state.is_running else "Complete" if pipeline_state.is_complete else "Pending"

    progress_html = f"""
    <div class="pipeline-progress-wrap">
        <div class="pipeline-progress">
            {segments_html}
        </div>
        <div class="pipeline-progress-meta">
            <span>{completed}/{total} agents complete</span>
            <span>{active_label}</span>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

    timeline_state = "complete" if pipeline_state.is_complete else "error" if pipeline_state.has_error else "running"
    timeline_html = f"""
    <div class="pipeline-timeline state-{timeline_state}" aria-hidden="true">
        <div class="pipeline-timeline-fill" style="width:{progress_pct:.2f}%;"></div>
    </div>
    """
    st.markdown(timeline_html, unsafe_allow_html=True)

    if pipeline_state.is_complete:
        st.markdown(
            """
            <div class="pipeline-easter-egg" aria-hidden="true">
                <span class="egg-dot dot-1"></span>
                <span class="egg-dot dot-2"></span>
                <span class="egg-dot dot-3"></span>
                <span class="egg-dot dot-4"></span>
                <span class="egg-dot dot-5"></span>
                <span class="egg-dot dot-6"></span>
                <span class="egg-dot dot-7"></span>
                <span class="egg-dot dot-8"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_card(label: str, value: str, icon: str = ""):
    """Render a small metric display card."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_cards(pipeline_state: PipelineState):
    """Render the full horizontal row of 6 agent cards with arrows between them."""
    agents_config = config.AGENTS

    # Use columns: card, arrow, card, arrow, ... card
    # 6 cards + 5 arrows = 11 columns, but we use unequal widths
    cols = st.columns([2.35, 0.16, 2.35, 0.16, 2.35, 0.16, 2.35, 0.16, 2.35, 0.16, 2.35], gap="small")

    for i, (agent_status, agent_cfg) in enumerate(zip(pipeline_state.agents, agents_config)):
        col_idx = i * 2  # 0, 2, 4, 6, 8, 10

        with cols[col_idx]:
            render_agent_card(agent_status, agent_cfg)

        # Arrow between cards (not after the last card)
        if i < len(pipeline_state.agents) - 1:
            arrow_col_idx = col_idx + 1
            with cols[arrow_col_idx]:
                st.markdown("<div style='height:148px;'></div>", unsafe_allow_html=True)
                prev_state = agent_status.state.value
                next_state = pipeline_state.agents[i + 1].state.value
                next_color = agents_config[i + 1].get("color", "#3b82f6")
                render_arrow(prev_state, next_state, next_color)
