"""
Streamlit UI for the Multi-agent DevOps Incident Analysis Suite.
Upload or select sample logs, run analysis, view results and cookbook.
"""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SAMPLE_LOGS_DIR, OPENROUTER_API_KEY
from agents.workflow import build_incident_graph

_DEBUG_LOG = Path(__file__).resolve().parent / ".cursor" / "debug.log"


st.set_page_config(
    page_title="DevOps Incident Analysis",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a polished DevOps dashboard look
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #00D4AA;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(145deg, #1A1D24 0%, #161922 100%);
        border: 1px solid #2D333B;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .severity-critical { color: #F87171; font-weight: 600; }
    .severity-high { color: #FBBF24; font-weight: 600; }
    .severity-medium { color: #60A5FA; font-weight: 600; }
    .severity-low { color: #94A3B8; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #1A1D24;
        border-radius: 8px;
        padding: 10px 20px;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] { background: #00D4AA; color: #0E1117; }
    blockquote { border-left: 4px solid #00D4AA; padding-left: 1rem; margin: 1rem 0; color: #94A3B8; }
</style>
""", unsafe_allow_html=True)


def get_sample_log_files():
    if not SAMPLE_LOGS_DIR.exists():
        return []
    return sorted([f.name for f in SAMPLE_LOGS_DIR.iterdir() if f.is_file()])


def load_sample_content(filename: str) -> str:
    path = SAMPLE_LOGS_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def run_analysis(raw_logs: str):
    graph = build_incident_graph()
    initial = {
        "raw_logs": raw_logs,
        "parsed_entries": [],
        "classified_issues": [],
        "remediations": [],
        "cookbook": "",
        "notifications_sent": False,
        "jira_ticket_id": None,
    }
    return graph.invoke(initial)


def main():
    st.markdown('<p class="main-header">🔧 DevOps Incident Analysis Suite</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Upload ops logs or pick a sample. Multi-agent analysis: parse → classify → remediate → cookbook → Slack/JIRA.</p>',
        unsafe_allow_html=True,
    )

    if not OPENROUTER_API_KEY:
        st.warning("Set `OPENROUTER_API_KEY` in `.env` to run LLM-based classification and cookbook generation.")

    sidebar = st.sidebar
    sidebar.header("Input")
    input_mode = sidebar.radio("Log source", ["Upload file", "Select sample", "Paste text"], index=1)

    raw_logs = ""
    if input_mode == "Upload file":
        uploaded = st.sidebar.file_uploader("Choose a log file", type=["log", "txt", "json"])
        if uploaded:
            raw_logs = uploaded.read().decode("utf-8", errors="replace")
            st.sidebar.success(f"Loaded {len(raw_logs)} characters")
    elif input_mode == "Select sample":
        samples = get_sample_log_files()
        if not samples:
            st.sidebar.info("No sample logs in `sample_logs/`. Add .log or .txt files.")
        else:
            chosen = st.sidebar.selectbox("Sample log", samples)
            if chosen:
                raw_logs = load_sample_content(chosen)
                st.sidebar.success(f"Loaded: {chosen}")
    else:
        raw_logs = st.sidebar.text_area("Paste log content", height=200, placeholder="Paste logs here...")

    if not raw_logs.strip():
        st.info("Upload a file, select a sample, or paste log content to run analysis.")
        return

    st.divider()
    if st.button("Run incident analysis", type="primary", use_container_width=True):
        with st.spinner("Running pipeline: parse → classify → remediate → cookbook..."):
            try:
                result = run_analysis(raw_logs)
                # #region agent log
                try:
                    issues = result.get("classified_issues") or []
                    first_sev = issues[0].get("severity") if issues and isinstance(issues[0], dict) else None
                    with open(_DEBUG_LOG, "a") as f:
                        f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "app.py:run_analysis", "message": "invoke result", "data": {"notifications_sent": result.get("notifications_sent"), "issues_count": len(issues), "first_severity": first_sev}, "hypothesisId": "A,B,E"}) + "\n")
                except Exception:
                    pass
                # #endregion
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                raise
        st.session_state["analysis_result"] = result
        st.success("Analysis complete.")

    if "analysis_result" not in st.session_state:
        return

    state = st.session_state["analysis_result"]
    parsed = state.get("parsed_entries") or []
    issues = state.get("classified_issues") or []
    remediations = state.get("remediations") or []
    cookbook = state.get("cookbook") or ""
    notifications_sent = state.get("notifications_sent", False)
    jira_ticket_id = state.get("jira_ticket_id")

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Parsed entries", len(parsed))
    col2.metric("Issues", len(issues))
    col3.metric("Remediations", len(remediations))
    col4.metric("Slack", "Sent" if notifications_sent else "—")
    col5.metric("JIRA", jira_ticket_id or "—")

    # Tabs: Parsed | Issues | Remediations | Cookbook
    tab1, tab2, tab3, tab4 = st.tabs(["Parsed logs", "Classified issues", "Remediations", "Cookbook"])

    with tab1:
        for i, e in enumerate(parsed[:100]):
            sev = (e.get("severity") or "INFO").upper()
            ts = e.get("timestamp") or "—"
            svc = e.get("service") or "—"
            msg = (e.get("message") or "")[:500]
            st.markdown(f"**{ts}** `{sev}` **{svc}** — {msg}")
        if len(parsed) > 100:
            st.caption(f"Showing first 100 of {len(parsed)} entries.")

    with tab2:
        for i, iss in enumerate(issues):
            sev = (iss.get("severity") or "MEDIUM").upper()
            cls = f"severity-{sev.lower()}"
            st.markdown(f'<span class="{cls}">[{sev}]</span> **{iss.get("summary", "—")}**', unsafe_allow_html=True)
            st.caption(f"Category: {iss.get('category')} | Subcategory: {iss.get('subcategory')} | Services: {iss.get('affected_services')}")
            st.json(iss)
            st.divider()

    with tab3:
        for r in remediations:
            st.subheader(r.get("issue_summary", "—"))
            steps = r.get("steps") or []
            for j, step in enumerate(steps, 1):
                st.markdown(f"{j}. {step}")
            if r.get("time_estimate"):
                st.caption(f"Estimate: {r['time_estimate']}")
            st.divider()

    with tab4:
        st.markdown(cookbook if cookbook else "*No cookbook generated.*")


if __name__ == "__main__":
    main()
