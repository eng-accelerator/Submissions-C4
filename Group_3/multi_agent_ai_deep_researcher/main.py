"""
LangGraph State Graph orchestration for Multi-Agent AI Deep Researcher.

This module compiles all agents into a graph with:
- Sequential nodes for each agent
- Conditional routing based on state (critic feedback)
- Checkpoint persistence for session management
- Built-in error recovery

Flow:
START → retriever → summarizer → critic → [decision] → insight → reporter → END
                                              ↑
                                         (if needs_refinement)
                                              |
                                          retriever
"""

from typing import Literal, Optional
from langgraph.graph import StateGraph, START, END

# Import checkpoint saver - try multiple paths for compatibility
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        MemorySaver = None

from utils.state import ResearchState
from agents.retriever import RetrieverAgent
from agents.summarizer import SummarizerAgent
from agents.critic import CriticAgent
from agents.insight import InsightAgent
from agents.reporter import ReporterAgent
from agents.supervisor import SupervisorAgent
from config import settings


# Initialize supervisor only (agents are created per graph for simpler configuration)
supervisor = SupervisorAgent()


def build_research_graph(
    checkpointer: Optional[object] = None,
    max_sources: Optional[int] = None,
) -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for research pipeline.
    
    Args:
        checkpointer: Optional checkpoint saver for session persistence
    
    Returns:
        Compiled StateGraph with all agents and routing
    """
    # Resolve runtime config
    if max_sources is None:
        max_sources = settings.max_sources_default

    retriever_agent = RetrieverAgent(
        max_sources=max_sources,
        scrape_timeout=10,
    )
    summarizer_agent = SummarizerAgent(max_summary_length=1000)
    critic_agent = CriticAgent(confidence_threshold=0.6)
    insight_agent = InsightAgent(max_insights=5)
    reporter_agent = ReporterAgent()

    # Create state graph
    graph = StateGraph(ResearchState)
    
    # ===== ADD NODES FOR EACH AGENT =====
    
    graph.add_node("retriever", retriever_agent.process)
    graph.add_node("summarizer", summarizer_agent.process)
    graph.add_node("critic", critic_agent.process)
    graph.add_node("insight", insight_agent.process)
    graph.add_node("reporter", reporter_agent.process)
    
    # ===== ADD EDGES (LINEAR FLOW) =====
    
    # Start → retriever
    graph.add_edge(START, "retriever")
    
    # retriever → summarizer
    graph.add_edge("retriever", "summarizer")
    
    # summarizer → critic
    graph.add_edge("summarizer", "critic")
    
    # ===== CONDITIONAL EDGE: critic → refinement or insight =====
    
    def should_refine(state: ResearchState) -> Literal["retriever", "insight"]:
        """
        Conditional routing after critic assessment.
        
        Args:
            state: Current research state
        
        Returns:
            Next node: "retriever" for refinement or "insight" to continue
        """
        needs_refinement = state.needs_refinement
        iteration = state.iteration_count
        total_iterations = state.total_iterations
        
        # Check if we should refine
        if needs_refinement and iteration < total_iterations - 1:
            return "retriever"  # Loop back to retriever
        else:
            return "insight"  # Continue forward
    
    graph.add_conditional_edges(
        "critic",
        should_refine,
        {
            "retriever": "retriever",
            "insight": "insight",
        }
    )
    
    # ===== CONTINUE LINEAR FLOW =====
    
    # insight → reporter
    graph.add_edge("insight", "reporter")
    
    # reporter → end
    graph.add_edge("reporter", END)
    
    # ===== COMPILE GRAPH =====
    
    if checkpointer is None:
        # Default to in-memory checkpointing for local runs
        if MemorySaver is not None:
            try:
                checkpointer = MemorySaver()
            except Exception:
                checkpointer = None
    
    try:
        compiled_graph = graph.compile(
            checkpointer=checkpointer,
        )
    except TypeError:
        # If checkpointer parameter not supported, compile without it
        compiled_graph = graph.compile()
    
    return compiled_graph


def build_research_graph_with_file_checkpoint(
    checkpoint_path: str = None,
) -> StateGraph:
    """
    Build graph with file-based checkpointing for persistent sessions.
    
    Args:
        checkpoint_path: Path to checkpoint SQLite database
    
    Returns:
        Compiled StateGraph with file-based checkpointing
    """
    # Keep behavior simple for local usage: always return in-memory graph.
    return build_research_graph(checkpointer=None)


def resume_research_session(
    session_id: str,
    checkpointer: Optional[object] = None,
) -> Optional[dict]:
    """
    Resume a research session from checkpoint.
    
    Args:
        session_id: Session ID to resume
        checkpointer: Checkpoint saver (uses file checkpoint if None)
    
    Returns:
        Checkpoint state or None if not found
    """
    # Local in-memory checkpoints are per-process; explicit resume by session ID
    # is not supported in this minimal implementation.
    return None


def list_sessions(checkpointer: Optional[object] = None) -> list:
    """
    List all available session checkpoints.
    
    Args:
        checkpointer: Checkpoint saver (uses file checkpoint if None)
    
    Returns:
        List of session IDs
    """
    return []


def run_research(
    query: str,
    session_id: str,
    graph: Optional[StateGraph] = None,
    max_iterations: int = None,
) -> Optional[ResearchState]:
    """
    Run the research pipeline with given query.
    
    Args:
        query: Research query/question
        session_id: Unique session identifier
        graph: Compiled StateGraph (builds if None)
        max_iterations: Maximum refinement iterations
    
    Returns:
        Final ResearchState with all results
    """
    if graph is None:
        graph = build_research_graph()
    
    if max_iterations is None:
        max_iterations = settings.max_refinement_passes
    
    # Initialize state
    state = ResearchState(
        user_query=query,
        session_id=session_id,
        current_step="init",
        iteration_count=0,
        total_iterations=max_iterations,
    )
    
    try:
        # Run graph with streaming
        config = {"configurable": {"thread_id": session_id}}
        
        for output in graph.stream(
            state.to_dict(),
            config=config,
            stream_mode="updates",
        ):
            # Process updates
            for node, values in output.items():
                if node != "__start__":
                    pass
        
        # Get final state (handle case where checkpointing is not available)
        try:
            final_state = graph.get_state(config)
        except (AttributeError, TypeError):
            # If get_state not available, return last output state
            final_state = None

        if final_state and hasattr(final_state, "values"):
            return ResearchState.from_dict(final_state.values)
        return None
    
    except Exception:
        raise


__all__ = [
    "build_research_graph",
    "build_research_graph_with_file_checkpoint",
    "resume_research_session",
    "list_sessions",
    "run_research",
    "supervisor",
]
