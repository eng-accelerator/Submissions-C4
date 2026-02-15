"""
utils/callbacks.py
===================
Streamlit progress tracking callbacks for the agent pipeline.

Provides a context-manager-based progress tracker that integrates
with Streamlit's st.status widget to show real-time agent activity.

USAGE:
    tracker = ProgressTracker()
    with tracker.agent_step("retriever"):
        # ... do work ...
        tracker.update_message("Found 6 sources")
"""

from __future__ import annotations

import time
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


# Agent metadata for display
AGENT_CONFIG = {
    "decomposer": {
        "name": "Query Decomposer",
        "icon": "🔍",
        "description": "Breaking down your research question...",
    },
    "retriever": {
        "name": "Retriever Agent",
        "icon": "🌐",
        "description": "Searching the web for sources...",
    },
    "analyzer": {
        "name": "Analysis Agent",
        "icon": "🔬",
        "description": "Analyzing and synthesizing findings...",
    },
    "fact_checker": {
        "name": "Fact-Checker Agent",
        "icon": "✅",
        "description": "Cross-validating claims and scoring confidence...",
    },
    "insight": {
        "name": "Insight Generator",
        "icon": "💡",
        "description": "Generating hypotheses and identifying trends...",
    },
    "reporter": {
        "name": "Report Builder",
        "icon": "📝",
        "description": "Compiling the final research report...",
    },
    "quality_gate": {
        "name": "Quality Gate",
        "icon": "🎯",
        "description": "Evaluating research quality...",
    },
}


@dataclass
class AgentStepResult:
    """Result of a single agent step for UI display."""
    agent_key: str
    agent_name: str
    icon: str
    status: str = "running"       # running, complete, error
    message: str = ""
    duration_seconds: float = 0.0
    details: dict = field(default_factory=dict)


class ProgressTracker:
    """
    Tracks agent pipeline progress for Streamlit UI display.

    Supports an optional live-write target (a Streamlit container)
    so that each agent's start/completion is rendered in real time.
    """

    def __init__(
        self,
        on_update: Optional[Callable] = None,
        live_container: Any = None,
    ):
        """
        Args:
            on_update: Optional callback invoked after each status change.
            live_container: A Streamlit container (e.g., from st.status)
                            to write live progress updates into.
        """
        self.steps: list[AgentStepResult] = []
        self.current_step: Optional[AgentStepResult] = None
        self.on_update = on_update
        self.start_time: float = time.time()
        self._live = live_container

    @contextmanager
    def agent_step(self, agent_key: str, custom_message: str = ""):
        """
        Context manager for tracking an agent step.

        Args:
            agent_key: Key from AGENT_CONFIG (e.g., 'retriever').
            custom_message: Override the default description.

        Yields:
            AgentStepResult for the current step.
        """
        config = AGENT_CONFIG.get(agent_key, {
            "name": agent_key,
            "icon": "⚙️",
            "description": f"Running {agent_key}...",
        })

        step = AgentStepResult(
            agent_key=agent_key,
            agent_name=config["name"],
            icon=config["icon"],
            status="running",
            message=custom_message or config["description"],
        )
        self.current_step = step
        self.steps.append(step)

        # Live UI: show the agent starting
        self._live_write(
            f"⏳ **{config['icon']} {config['name']}** — {step.message}"
        )
        self._notify()

        step_start = time.time()
        try:
            yield step
            step.status = "complete"
            step.duration_seconds = time.time() - step_start
            # Live UI: show completion
            self._live_write(
                f"✅ **{config['icon']} {config['name']}** — "
                f"{step.message} ({step.duration_seconds:.1f}s)"
            )
            logger.info(
                f"{config['icon']} {config['name']} completed "
                f"in {step.duration_seconds:.1f}s"
            )
        except Exception as e:
            step.status = "error"
            step.message = f"Error: {str(e)}"
            step.duration_seconds = time.time() - step_start
            self._live_write(
                f"❌ **{config['icon']} {config['name']}** — "
                f"{step.message} ({step.duration_seconds:.1f}s)"
            )
            logger.error(f"{config['icon']} {config['name']} failed: {e}")
            raise
        finally:
            self.current_step = None
            self._notify()

    def update_message(self, message: str):
        """Update the current step's message (shown on completion)."""
        if self.current_step:
            self.current_step.message = message
            self._notify()

    def total_duration(self) -> float:
        """Total elapsed time since tracker was created."""
        return time.time() - self.start_time

    def _live_write(self, text: str):
        """Write a line to the live Streamlit container if available."""
        if self._live:
            try:
                self._live.write(text)
            except Exception:
                pass

    def _notify(self):
        """Call the update callback if registered."""
        if self.on_update:
            try:
                self.on_update()
            except Exception:
                pass  # Don't let callback errors break the pipeline
