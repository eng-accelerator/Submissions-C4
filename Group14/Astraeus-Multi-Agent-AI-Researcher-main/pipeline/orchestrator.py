"""
Pipeline Orchestrator
━━━━━━━━━━━━━━━━━━━━
The "branch manager" that routes the research query through all 6 agents
in sequence, like a loan application flowing through the bank's processing
desks. Each agent reads from and writes to a shared context dict.

Pipeline order:
  1. Research Coordinator  → query analysis + expansion
  2. Contextual Retriever  → vector search + ranking
  3. Critical Analysis     → claim extraction + contradictions
  4. Fact-Checker          → credibility + cross-check
  5. Insight Generator     → themes + gaps + hypotheses
  6. Report Builder        → final report + citations
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import time
import traceback

from agents import coordinator, retriever, critical_analysis, fact_checker, insight_generator, report_builder


class AgentState(str, Enum):
    NOT_STARTED = "not_started"
    WAITING = "waiting"
    WORKING = "working"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentStatus:
    agent_id: str
    name: str
    state: AgentState = AgentState.NOT_STARTED
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    elapsed_seconds: float = 0.0
    output_summary: str = ""
    error_message: str = ""


@dataclass
class PipelineState:
    """Holds the entire pipeline state for UI rendering."""
    agents: list = field(default_factory=list)
    current_agent_index: int = -1
    pipeline_start_time: Optional[float] = None
    pipeline_end_time: Optional[float] = None
    total_elapsed: float = 0.0
    is_running: bool = False
    is_complete: bool = False
    has_error: bool = False
    context: Dict[str, Any] = field(default_factory=dict)


# ── Agent registry (order matters!) ───────────────────────────────────
AGENT_REGISTRY = [
    {"id": "coordinator",       "name": "Research Coordinator",  "run": coordinator.run},
    {"id": "retriever",         "name": "Contextual Retriever",  "run": retriever.run},
    {"id": "critical_analysis", "name": "Critical Analysis",     "run": critical_analysis.run},
    {"id": "fact_checker",      "name": "Fact-Checker",          "run": fact_checker.run},
    {"id": "insight_generator", "name": "Insight Generator",     "run": insight_generator.run},
    {"id": "report_builder",    "name": "Report Builder",        "run": report_builder.run},
]


def create_pipeline_state() -> PipelineState:
    """Initialize a fresh pipeline state."""
    agents = [
        AgentStatus(agent_id=a["id"], name=a["name"])
        for a in AGENT_REGISTRY
    ]
    return PipelineState(agents=agents)


def run_pipeline(
    query: str,
    state: PipelineState,
    on_state_change: Optional[Callable[[PipelineState], None]] = None,
    initial_context: Optional[Dict[str, Any]] = None,
    before_agent_run: Optional[Callable[[str], None]] = None,
    after_agent_run: Optional[Callable[[str], None]] = None,
) -> PipelineState:
    """
    Run the full 6-agent pipeline sequentially.

    Args:
        query: The user's research query
        state: PipelineState to mutate and report
        on_state_change: Callback fired after each state change (for UI updates)
        initial_context: Optional extra context keys to seed the pipeline
        before_agent_run: Optional callback called with agent_id before each run
        after_agent_run: Optional callback called with agent_id after each run

    Returns:
        The final PipelineState with all results in state.context
    """
    state.is_running = True
    state.is_complete = False
    state.has_error = False
    state.pipeline_start_time = time.time()
    state.context = {"query": query}
    if initial_context:
        state.context.update(initial_context)

    _notify(state, on_state_change)

    for idx, agent_def in enumerate(AGENT_REGISTRY):
        agent_status = state.agents[idx]
        state.current_agent_index = idx

        # ── Set next agent to "Waiting" ───────────────────────────────
        agent_status.state = AgentState.WAITING
        agent_status.progress = 0.0
        _notify(state, on_state_change)

        # ── Set to "Working" ──────────────────────────────────────────
        agent_status.state = AgentState.WORKING
        agent_status.start_time = time.time()
        agent_status.progress = 0.1
        _notify(state, on_state_change)

        try:
            if before_agent_run:
                before_agent_run(agent_def["id"])
            # ── Run the agent ─────────────────────────────────────────
            state.context = agent_def["run"](state.context)

            # ── Mark complete ─────────────────────────────────────────
            agent_status.end_time = time.time()
            agent_status.elapsed_seconds = round(agent_status.end_time - agent_status.start_time, 2)
            agent_status.state = AgentState.COMPLETE
            agent_status.progress = 1.0

            # Extract a short summary from agent output
            output_key = f"{agent_def['id']}_output"
            output = state.context.get(output_key, {})
            agent_status.output_summary = _summarize_output(agent_def["id"], output)

            _notify(state, on_state_change)

        except Exception as e:
            agent_status.state = AgentState.ERROR
            agent_status.error_message = str(e)
            agent_status.end_time = time.time()
            agent_status.elapsed_seconds = round(agent_status.end_time - agent_status.start_time, 2)
            state.has_error = True
            state.is_running = False

            # Store traceback for debugging
            state.context["pipeline_error"] = {
                "agent": agent_def["id"],
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            _notify(state, on_state_change)
            return state
        finally:
            if after_agent_run:
                after_agent_run(agent_def["id"])

    # ── Pipeline complete ─────────────────────────────────────────────
    state.pipeline_end_time = time.time()
    state.total_elapsed = round(state.pipeline_end_time - state.pipeline_start_time, 2)
    state.is_running = False
    state.is_complete = True
    _notify(state, on_state_change)

    return state


def _notify(state: PipelineState, callback: Optional[Callable]):
    """Update total elapsed and call the UI callback."""
    if state.pipeline_start_time:
        state.total_elapsed = round(time.time() - state.pipeline_start_time, 2)
    if callback:
        callback(state)


def _summarize_output(agent_id: str, output: dict) -> str:
    """Generate a short human-readable summary for each agent's output."""
    if not output:
        return "No output"

    summaries = {
        "coordinator": lambda o: (
            f"Expanded to {len(o.get('expanded_queries', []))} queries | "
            f"Intent: {o.get('analysis', {}).get('intent', '?')}"
        ),
        "retriever": lambda o: (
            f"Retrieved {o.get('num_chunks', 0)} chunks + "
            f"{o.get('web_results_count', 0)} web results"
        ),
        "critical_analysis": lambda o: (
            f"Extracted {o.get('total_claims', 0)} claims | "
            f"{o.get('contradictions_found', 0)} contradictions"
        ),
        "fact_checker": lambda o: (
            f"Verified: {o.get('verified', 0)} | "
            f"Disputed: {o.get('disputed', 0)} | "
            f"Total: {o.get('total_checked', 0)}"
        ),
        "insight_generator": lambda o: (
            f"{o.get('themes_found', 0)} themes | "
            f"{o.get('gaps_identified', 0)} gaps | "
            f"{o.get('hypotheses_generated', 0)} hypotheses"
        ),
        "report_builder": lambda o: (
            f"Report: {o.get('word_count', 0)} words | "
            f"{len(o.get('sections', []))} sections"
        ),
    }

    summarizer = summaries.get(agent_id, lambda o: str(o)[:80])
    try:
        return summarizer(output)
    except Exception:
        return "Output generated"
