"""
Retrieval Waterfall Visualization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shows the stages from query → dense candidates → re-rank → final chunks.
Like tracking a bank transfer through clearing stages: Initiated → Processing
→ Verified → Settled. Each stage narrows the funnel.
"""

from __future__ import annotations
from typing import Dict, Any
import streamlit as st
import plotly.graph_objects as go


def render_retrieval_waterfall(context: Dict[str, Any]):
    """
    Render the retrieval waterfall/funnel visualization.

    Expected context keys:
      - retrieval_metadata: dict with 'stage_counts'
      - source_distribution: dict
    """
    metadata = context.get("retrieval_metadata", {})
    stage_counts = metadata.get("stage_counts", {})
    source_dist = context.get("source_distribution", {})

    if not stage_counts:
        st.info("No retrieval data available yet.")
        return

    # ── Waterfall/Funnel Chart ────────────────────────────────────────
    stages = [
        ("Queries Sent", stage_counts.get("queries", 0)),
        ("Dense Candidates", stage_counts.get("dense_candidates", 0)),
        ("After Re-ranking", stage_counts.get("after_rerank", 0)),
        ("Final Chunks", stage_counts.get("final_chunks", 0)),
    ]

    stage_names = [s[0] for s in stages]
    stage_values = [s[1] for s in stages]

    # Colors from wide to narrow
    colors = ["#60a5fa", "#818cf8", "#a78bfa", "#22c55e"]

    fig = go.Figure()

    fig.add_trace(go.Funnel(
        y=stage_names,
        x=stage_values,
        textinfo="value+percent initial",
        marker=dict(color=colors),
        connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
        textfont=dict(size=13, color="white"),
    ))

    fig.update_layout(
        title=dict(
            text="Retrieval Waterfall — From Queries to Final Chunks",
            font=dict(size=14, color='#94a3b8'),
        ),
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        height=350,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Source Distribution Bar ───────────────────────────────────────
    if source_dist:
        st.markdown("##### Source Distribution")
        source_names = list(source_dist.keys())
        source_counts = list(source_dist.values())
        total = sum(source_counts) if source_counts else 1

        source_colors = {
            "arxiv": "#3b82f6",
            "blog": "#f59e0b",
            "documentation": "#22c55e",
            "news": "#a78bfa",
            "web (Tavily)": "#ec4899",
            "web": "#ec4899",
            "government": "#14b8a6",
            "unknown": "#6b7280",
        }

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=source_counts,
            y=source_names,
            orientation='h',
            marker=dict(
                color=[source_colors.get(s, "#6b7280") for s in source_names],
                line=dict(width=0),
            ),
            text=[f"{c} ({100*c/total:.0f}%)" for c in source_counts],
            textposition='auto',
            textfont=dict(color='white', size=12),
        ))

        fig2.update_layout(
            title=dict(text="Results by Source", font=dict(size=13, color='#94a3b8')),
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
        )

        st.plotly_chart(fig2, use_container_width=True)
