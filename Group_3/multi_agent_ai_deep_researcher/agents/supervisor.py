"""
Supervisor Agent for the Multi-Agent AI Deep Researcher.

This is a deterministic routing agent that:
1. Routes to appropriate agents based on state flags
2. Manages the research workflow
3. Determines when to refine vs continue
4. No LLM needed - logic-based routing
"""

from typing import Dict, Any
from utils.state import ResearchState, StateUpdate


class SupervisorAgent:
    """
    Deterministic supervisor for agent routing.
    
    Routes:
    - START → retriever
    - retriever → summarizer  
    - summarizer → critic
    - critic → (retriever if needs_refinement else insight)
    - insight → reporter
    - reporter → END
    """
    
    def __init__(self):
        """Initialize the Supervisor Agent."""
        self.name = "supervisor"
    
    def route_next_agent(self, state: ResearchState) -> str:
        """
        Determine next agent based on current state.
        
        Args:
            state: Current research state
        
        Returns:
            Next agent name or "end" if done
        """
        current_step = state.current_step
        iteration = state.iteration_count
        total_iterations = state.total_iterations
        needs_refinement = state.needs_refinement
        
        # Initial state - start retrieval
        if current_step == "init":
            return "retriever"
        
        # After retrieval - summarize
        if current_step == "retriever":
            return "summarizer"
        
        # After summarization - critique
        if current_step == "summarizer":
            return "critic"
        
        # After critique - conditional routing
        if current_step == "critic":
            # Check if refinement is needed and iterations available
            if needs_refinement and iteration < total_iterations - 1:
                return "retriever"  # Loop back for refinement
            else:
                return "insight"  # Continue to insight
        
        # After insight extraction - generate report
        if current_step == "insight":
            return "reporter"
        
        # After report generation - end
        if current_step == "reporter":
            return "end"
        
        # Unknown state - end
        return "end"
    
    def should_continue(self, state: ResearchState) -> bool:
        """
        Determine if pipeline should continue.
        
        Args:
            state: Current research state
        
        Returns:
            True if pipeline should continue, False if done
        """
        next_agent = self.route_next_agent(state)
        return next_agent != "end"
    
    def get_routing_info(self, state: ResearchState) -> Dict[str, Any]:
        """
        Get detailed routing information for debugging.
        
        Args:
            state: Current research state
        
        Returns:
            Dict with routing details
        """
        next_agent = self.route_next_agent(state)
        
        return {
            "current_step": state.current_step,
            "next_step": next_agent,
            "iteration": state.iteration_count,
            "total_iterations": state.total_iterations,
            "needs_refinement": state.needs_refinement,
            "reason": self._get_routing_reason(state, next_agent),
        }
    
    def _get_routing_reason(self, state: ResearchState, next_agent: str) -> str:
        """
        Get human-readable reason for routing decision.
        
        Args:
            state: Current research state
            next_agent: Next agent to route to
        
        Returns:
            Reason string
        """
        current_step = state.current_step
        
        if next_agent == "retriever" and current_step == "critic":
            return "Refinement needed - iterating retrieval"
        
        if next_agent == "insight" and current_step == "critic":
            return "Critique complete - proceeding to insight extraction"
        
        if next_agent == "end":
            return "Pipeline complete"
        
        routing_map = {
            "init": "retriever",
            "retriever": "summarizer",
            "summarizer": "critic",
            "critic": "routing based on needs_refinement",
            "insight": "reporter",
            "reporter": "end",
        }
        
        # Find the route
        route = routing_map.get(current_step, "unknown")
        return f"Routing from {current_step} → {next_agent}"


__all__ = ["SupervisorAgent"]
