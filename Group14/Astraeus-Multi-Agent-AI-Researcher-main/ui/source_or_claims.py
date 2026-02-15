"""
Claims & Evidence Visualization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shows claims extracted by Critical Analysis and Fact-Checker with
strength indicators. Think of it like a bank's audit trail —
every claim is backed by evidence, rated for credibility.
"""

from __future__ import annotations
from typing import Dict, Any, List
import streamlit as st
import plotly.graph_objects as go


def render_claims_evidence(context: Dict[str, Any]):
    """
    Render the claim/evidence list with strength indicators.

    Expected context keys:
      - fact_check_results: List[dict]
      - credibility_summary: dict
      - evidence_chains: List[dict]
    """
    fact_results = context.get("fact_check_results", [])
    credibility = context.get("credibility_summary", {})
    evidence_chains = context.get("evidence_chains", [])

    if not fact_results:
        st.info("No fact-check data available yet.")
        return

    # ── Verdict Distribution Donut ────────────────────────────────────
    verdict_breakdown = credibility.get("verdict_breakdown", {})
    if verdict_breakdown:
        _render_verdict_donut(verdict_breakdown)

    # ── Claims Table ──────────────────────────────────────────────────
    st.markdown("##### Fact-Check Results")

    verdict_icons = {
        "verified": "✅",
        "partially_verified": "🟡",
        "unverified": "❓",
        "disputed": "⚠️",
    }

    strength_colors = {
        "strong": "#22c55e",
        "moderate": "#f59e0b",
        "weak": "#ef4444",
    }

    for i, result in enumerate(fact_results[:10]):
        verdict = result.get("verdict", "unknown")
        icon = verdict_icons.get(verdict, "❔")
        score = result.get("credibility_score", 0)
        claim_text = result.get("claim", "")[:150]
        evidence_type = result.get("evidence_type", "unknown")
        source_cred = result.get("source_credibility", "unknown")
        supporting = result.get("supporting_sources", 0)

        # Score bar color
        if score >= 0.7:
            bar_color = "#22c55e"
        elif score >= 0.5:
            bar_color = "#f59e0b"
        else:
            bar_color = "#ef4444"

        bar_width = int(score * 100)

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:12px;margin:8px 0;border-left:3px solid {bar_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-size:0.85rem;font-weight:600;">{icon} {verdict.replace('_',' ').title()}</span>
                <span style="font-size:0.75rem;color:#94a3b8;">Score: {score:.2f} | {evidence_type} | {supporting} supporting source(s)</span>
            </div>
            <div style="font-size:0.8rem;color:#cbd5e1;margin-bottom:8px;">{claim_text}</div>
            <div style="background:rgba(255,255,255,0.1);border-radius:4px;height:6px;overflow:hidden;">
                <div style="width:{bar_width}%;height:100%;background:{bar_color};border-radius:4px;transition:width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Evidence Chains ───────────────────────────────────────────────
    if evidence_chains:
        with st.expander("🔗 Evidence Chains"):
            for chain in evidence_chains[:6]:
                strength = chain.get("strength", "unknown")
                color = strength_colors.get(strength, "#6b7280")
                st.markdown(f"""
                <div style="border-left:3px solid {color};padding:8px 12px;margin:6px 0;font-size:0.8rem;">
                    <strong>{chain.get('claim', '')[:120]}</strong><br>
                    📎 Source: <code>{chain.get('source_id', '?')}</code> |
                    Confidence: {chain.get('confidence', 0)} |
                    Type: {chain.get('evidence_type', '?')} |
                    Strength: <span style="color:{color};">{strength}</span>
                </div>
                """, unsafe_allow_html=True)


def _render_verdict_donut(verdict_breakdown: Dict[str, int]):
    """Render a donut chart of verdict distribution."""
    labels = []
    values = []
    colors_map = {
        "verified": "#22c55e",
        "partially_verified": "#f59e0b",
        "unverified": "#6b7280",
        "disputed": "#ef4444",
    }
    colors = []

    for verdict, count in verdict_breakdown.items():
        labels.append(verdict.replace("_", " ").title())
        values.append(count)
        colors.append(colors_map.get(verdict, "#6b7280"))

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='rgba(0,0,0,0.3)', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, color='white'),
    )])

    total = sum(values)
    fig.update_layout(
        title=dict(text="Claim Verdicts", font=dict(size=13, color='#94a3b8')),
        annotations=[dict(text=f"{total}<br>Claims", x=0.5, y=0.5, font_size=16,
                         font_color='#94a3b8', showarrow=False)],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)
