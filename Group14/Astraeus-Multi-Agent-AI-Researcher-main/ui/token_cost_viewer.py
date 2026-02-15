"""
Token and cost tracking visualization for post-pipeline analysis.
"""

from __future__ import annotations

from typing import Dict, Any, List
import streamlit as st
import pandas as pd


def render_token_cost_viewer(context: Dict[str, Any]) -> None:
    """Render token and cost summary + per-agent breakdown."""
    tracking = context.get("token_tracking", {})
    by_agent: Dict[str, Dict[str, Any]] = tracking.get("by_agent", {})
    totals = tracking.get("totals", {})

    if not by_agent:
        st.info("No token or cost data available for this run.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Input Tokens", _fmt_int(totals.get("input_tokens", 0)))
    with c2:
        st.metric("Total Output Tokens", _fmt_int(totals.get("output_tokens", 0)))
    with c3:
        st.metric("Total Tokens", _fmt_int(totals.get("total_tokens", 0)))
    with c4:
        st.metric("Total Cost", f"${totals.get('cost_usd', 0.0):.4f}")

    rows: List[Dict[str, Any]] = []
    for item in by_agent.values():
        rows.append(
            {
                "Agent": item.get("name", item.get("agent_id", "Unknown")),
                "Input Tokens": item.get("input_tokens", 0),
                "Output Tokens": item.get("output_tokens", 0),
                "Total Tokens": item.get("total_tokens", 0),
                "Cost (USD)": round(item.get("cost_usd", 0.0), 4),
                "LLM Calls": item.get("llm_calls", 0),
                "Time (s)": round(item.get("elapsed_seconds", 0.0), 2),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Cost (USD)", "Total Tokens"], ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

    most_expensive = tracking.get("most_expensive_agent", {})
    if most_expensive:
        st.caption(
            f"Most expensive agent: {most_expensive.get('name', 'Unknown')} "
            f"(${most_expensive.get('cost_usd', 0.0):.4f})"
        )

    with st.expander("Advanced details", expanded=False):
        retrieved_chunks = context.get("retrieved_chunks", [])
        rag_context_est_tokens = int(
            sum(len(c.get("text", "")) for c in retrieved_chunks) / 4
        ) if retrieved_chunks else 0
        st.markdown(
            f"- **LLM Calls:** {totals.get('llm_calls', 0)}\n"
            f"- **Average Cost per LLM Call:** "
            f"${_safe_div(totals.get('cost_usd', 0.0), totals.get('llm_calls', 0)):.4f}\n"
            f"- **Average Cost per 1K Tokens:** "
            f"${_safe_div(totals.get('cost_usd', 0.0) * 1000, max(totals.get('total_tokens', 0), 1)):.4f}\n"
            f"- **Estimated RAG Context Tokens:** {rag_context_est_tokens:,} "
            f"(character-based estimate)"
        )


def _fmt_int(value: int) -> str:
    return f"{int(value):,}"


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0
