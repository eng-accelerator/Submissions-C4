"""
Base agent interface for the Multi-Agent AI Deep Researcher.

All specialized agents (Retriever, Summarizer, Critic, etc.) inherit from this
base class to ensure consistent behavior, error handling, and state management.

The base class provides:
- Standard process() method signature
- Error handling and retry logic
- State validation using Pydantic
- Execution timing and metrics
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time

from utils.state import ResearchState, StateUpdate


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.
    
    Defines standard interface and common functionality that all agents must implement.
    Each agent processes the current state and returns an update dict.
    """
    
    def __init__(self, name: str):
        """
        Initialize the agent.
        
        Args:
            name: Agent name (e.g., 'retriever', 'summarizer')
        """
        self.name = name
    
    @abstractmethod
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute the agent's core logic.
        
        This is the main processing method that subclasses must implement.
        
        Args:
            state: Current research state (Pydantic model)
        
        Returns:
            Dictionary with state updates (keys match ResearchState fields)
        """
        pass
    
    def process(self, state: Dict[str, Any]) -> StateUpdate:
        """
        Process the state through this agent with error handling.
        
        This is the method called by LangGraph. It wraps execute() with:
        - Timing and metrics collection
        - Error handling
        - State validation
        - Execution tracking
        
        Args:
            state: Current research state as dict (from LangGraph)
        
        Returns:
            State update dictionary
        """
        start_time = time.time()
        
        try:
            # Convert dict to Pydantic model with validation
            if isinstance(state, dict):
                research_state = ResearchState.from_dict(state)
            else:
                research_state = state
            
            # Execute agent logic
            result = self.execute(research_state)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Add execution metadata
            if "execution_metadata" not in result:
                result["execution_metadata"] = {}
            result["execution_metadata"][self.name] = {
                "duration_ms": execution_time_ms,
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Agent {self.name} failed: {str(e)}"
            
            # Return graceful degradation with error message
            return {
                "error_messages": [error_msg],
                "current_step": self.name,
            }
    
    def _validate_input(self, state: ResearchState) -> None:
        """
        Validate input state before processing.
        
        Override in subclasses to add agent-specific validation.
        
        Args:
            state: State to validate
        
        Raises:
            ValueError: If state is invalid
        """
        # Base validation - ensure required fields exist
        if not state.user_query:
            raise ValueError("user_query is required")
        if not state.session_id:
            raise ValueError("session_id is required")


__all__ = ["BaseAgent"]
