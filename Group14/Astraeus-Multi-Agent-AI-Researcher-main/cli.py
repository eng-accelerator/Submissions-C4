#!/usr/bin/env python3
"""
Astraeus CLI — Run the research pipeline from the terminal.

Usage:
    python cli.py "What is retrieval-augmented generation?"
    python cli.py "Compare transformers vs RNNs" --output report.md
    python cli.py "Explain RLHF" --mode hybrid --model anthropic/claude-3-haiku
    python cli.py --list-agents
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from pipeline.orchestrator import (
    create_pipeline_state,
    run_pipeline,
    AgentState,
    AGENT_REGISTRY,
)


# ── ANSI colors for terminal output ─────────────────────────────────────
class _C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        for attr in ("BOLD", "DIM", "GREEN", "CYAN", "YELLOW", "RED", "MAGENTA", "RESET"):
            setattr(cls, attr, "")


def _print_banner():
    print(f"""
{_C.CYAN}{_C.BOLD}╔══════════════════════════════════════════════════════╗
║  Astraeus — Multi-Agent AI Deep Researcher (CLI)    ║
║  6 Agents · RAG-Powered · Pipeline Architecture     ║
╚══════════════════════════════════════════════════════╝{_C.RESET}
""")


def _print_agent_status(agent_id: str, name: str, state: str, elapsed: float = 0.0, summary: str = ""):
    icons = {
        AgentState.NOT_STARTED: f"{_C.DIM}○{_C.RESET}",
        AgentState.WAITING: f"{_C.YELLOW}◌{_C.RESET}",
        AgentState.WORKING: f"{_C.CYAN}◉{_C.RESET}",
        AgentState.COMPLETE: f"{_C.GREEN}●{_C.RESET}",
        AgentState.ERROR: f"{_C.RED}✗{_C.RESET}",
    }
    icon = icons.get(state, "?")
    elapsed_str = f" ({elapsed:.1f}s)" if elapsed > 0 else ""
    summary_str = f"  {_C.DIM}{summary}{_C.RESET}" if summary else ""
    print(f"  {icon} {name:<24}{elapsed_str}{summary_str}")


def _on_state_change(state):
    """Callback for real-time progress updates in verbose mode."""
    pass  # Updates are printed after each agent completes


def list_agents():
    """Print the agent registry."""
    print(f"\n{_C.BOLD}Astraeus Agent Pipeline:{_C.RESET}\n")
    for i, agent in enumerate(AGENT_REGISTRY, 1):
        cfg = next((a for a in config.AGENTS if a["id"] == agent["id"]), {})
        subtitle = cfg.get("subtitle", "")
        print(f"  {i}. {_C.BOLD}{agent['name']}{_C.RESET}")
        if subtitle:
            print(f"     {_C.DIM}{subtitle}{_C.RESET}")
    print()


def run_research(query: str, mode: str = "hybrid", model: str | None = None,
                 output_file: str | None = None, verbose: bool = False,
                 json_output: bool = False):
    """Run the full research pipeline and print results."""

    # Override model if specified
    if model:
        config.LLM_MODEL = model

    if not json_output:
        _print_banner()
        print(f"  {_C.BOLD}Query:{_C.RESET} {query}")
        print(f"  {_C.DIM}Model: {config.LLM_MODEL} | Mode: {mode}{_C.RESET}")
        print(f"\n{_C.BOLD}Pipeline:{_C.RESET}\n")

    # Build initial context with retrieval mode
    initial_context = {"retrieval_mode": mode}

    state = create_pipeline_state()
    start = time.time()

    # Run with progress callback
    def after_agent(agent_id: str):
        if json_output:
            return
        idx = next(i for i, a in enumerate(AGENT_REGISTRY) if a["id"] == agent_id)
        agent_status = state.agents[idx]
        _print_agent_status(
            agent_id,
            AGENT_REGISTRY[idx]["name"],
            agent_status.state,
            agent_status.elapsed_seconds,
            agent_status.output_summary,
        )

    final_state = run_pipeline(
        query=query,
        state=state,
        initial_context=initial_context,
        after_agent_run=after_agent,
    )

    total_time = time.time() - start

    if final_state.has_error:
        err = final_state.context.get("pipeline_error", {})
        if json_output:
            print(json.dumps({"error": err.get("error", "Unknown"), "agent": err.get("agent", "?")}))
        else:
            print(f"\n  {_C.RED}Pipeline failed at {err.get('agent', '?')}: {err.get('error', 'Unknown')}{_C.RESET}")
            if verbose and err.get("traceback"):
                print(f"\n{err['traceback']}")
        return 1

    # Extract report
    report = final_state.context.get("report_markdown", "")
    if not report:
        report = final_state.context.get("report_builder_output", {}).get("report", "No report generated.")

    if json_output:
        result = {
            "query": query,
            "model": config.LLM_MODEL,
            "mode": mode,
            "elapsed_seconds": round(total_time, 2),
            "agents": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "state": a.state.value,
                    "elapsed": a.elapsed_seconds,
                    "summary": a.output_summary,
                }
                for a in final_state.agents
            ],
            "report": report,
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'─' * 56}")
        print(f"  {_C.GREEN}{_C.BOLD}Pipeline complete{_C.RESET} in {total_time:.1f}s")
        print(f"{'─' * 56}\n")

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"  Report saved to: {_C.BOLD}{output_file}{_C.RESET}\n")
        else:
            print(report)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="astraeus",
        description="Astraeus — Multi-Agent AI Deep Researcher (CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python cli.py "What is RAG?"
  python cli.py "Compare GPT-4 vs Claude" --output report.md
  python cli.py "Explain RLHF" --mode hybrid --verbose
  python cli.py --list-agents
  python cli.py "Query" --json
""",
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Research query to investigate",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Save report to file instead of printing to stdout",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["local", "hybrid", "web"],
        default="hybrid",
        help="Retrieval mode: local (vector store only), hybrid (vector + web), web (web only). Default: hybrid",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL_ID",
        help=f"OpenRouter model ID to use (default: {config.LLM_MODEL})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including tracebacks on error",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all agents in the pipeline and exit",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_color:
        _C.disable()

    if args.list_agents:
        list_agents()
        return 0

    if not args.query:
        parser.print_help()
        return 1

    return run_research(
        query=args.query,
        mode=args.mode,
        model=args.model,
        output_file=args.output,
        verbose=args.verbose,
        json_output=args.json_output,
    )


if __name__ == "__main__":
    sys.exit(main())
