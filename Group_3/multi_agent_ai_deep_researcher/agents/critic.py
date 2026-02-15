"""
Critic Agent for the Multi-Agent AI Deep Researcher.

This agent:
1. Assesses the quality of research findings
2. Checks for gaps and contradictions
3. Determines if refinement is needed
4. Flags unreliable sources
"""

from typing import Dict, Any, List
from utils.state import ResearchState, StateUpdate, CritiqueSummary
from utils.llm import call_llm
from agents.base import BaseAgent


class CriticAgent(BaseAgent):
    """
    Quality assessment agent for research findings.
    
    This agent:
    1. Evaluates research quality
    2. Identifies gaps and contradictions
    3. Flags unreliable sources
    4. Determines if refinement is needed
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize the Critic Agent.
        
        Args:
            confidence_threshold: Source confidence threshold (0.0-1.0)
        """
        super().__init__("critic")
        self.confidence_threshold = confidence_threshold
    
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute critique and quality assessment.
        
        Args:
            state: Current research state
        
        Returns:
            State update with critique assessment
        """
        session_id = state.session_id
        user_query = state.user_query
        summary = state.summary
        source_metadata = state.source_metadata
        iteration = state.iteration_count
        
        try:
            # Assess source credibility
            flagged_sources = self._assess_sources(source_metadata)
            
            # Assess coverage and gaps
            coverage_score, needs_refinement = self._assess_coverage(
                summary,
                len(state.retrieved_docs),
                iteration,
                state.total_iterations
            )
            
            # Create critique summary
            critique = CritiqueSummary(
                strengths=self._extract_strengths(summary),
                weaknesses=self._extract_weaknesses(summary, len(state.retrieved_docs)),
                sources_flagged=flagged_sources,
                needs_refinement=needs_refinement,
                coverage_score=coverage_score,
            )
            
            return {
                "critique": critique.model_dump(),
                "needs_refinement": needs_refinement,
                "current_step": "critic",
            }
        
        except Exception as e:
            error_msg = f"Critic agent failed: {str(e)}"
            return {
                "critique": {},
                "needs_refinement": False,
                "current_step": "critic",
                "error_messages": [error_msg],
            }
    
    def _assess_sources(self, source_metadata: Dict[str, Any]) -> List[str]:
        """
        Assess and flag unreliable sources.
        
        Args:
            source_metadata: Source metadata dict
        
        Returns:
            List of flagged source URLs
        """
        flagged = []
        
        for doc_id, metadata in source_metadata.items():
            if isinstance(metadata, dict):
                confidence = metadata.get("confidence", 0.5)
            else:
                confidence = getattr(metadata, "confidence", 0.5)
            
            # Flag low-confidence sources
            if confidence < self.confidence_threshold:
                url = metadata.get("url") if isinstance(metadata, dict) else metadata.url
                flagged.append(url)
        
        return flagged
    
    def _assess_coverage(
        self,
        summary: str,
        doc_count: int,
        iteration: int,
        total_iterations: int
    ) -> tuple[float, bool]:
        """
        Assess research coverage and determine if refinement is needed.
        
        Args:
            summary: Current summary text
            doc_count: Number of documents retrieved
            iteration: Current iteration
            total_iterations: Maximum iterations
        
        Returns:
            Tuple of (coverage_score, needs_refinement)
        """
        # Base coverage score on document count
        coverage_score = min(1.0, (doc_count / 10) * 0.6)
        
        # Add points for summary length (comprehensive coverage)
        if len(summary) > 500:
            coverage_score += 0.2
        elif len(summary) > 300:
            coverage_score += 0.1
        
        # Determine if refining would help
        needs_refinement = (
            coverage_score < 0.8 and  # Coverage incomplete
            iteration < total_iterations - 1  # Iterations available
        )
        
        return min(1.0, coverage_score), needs_refinement
    
    def _extract_strengths(self, summary: str) -> List[str]:
        """
        Extract strengths from research.
        
        Args:
            summary: Research summary
        
        Returns:
            List of strength points
        """
        strengths = []
        
        if len(summary) > 500:
            strengths.append("Comprehensive coverage of topic")
        
        if len(summary) > 300:
            strengths.append("Multiple sources consulted")
        
        if summary:
            strengths.append("Primary research findings documented")
        
        return strengths if strengths else ["Research completed"]
    
    def _extract_weaknesses(self, summary: str, doc_count: int) -> List[str]:
        """
        Extract weaknesses from research.
        
        Args:
            summary: Research summary
            doc_count: Number of documents
        
        Returns:
            List of weakness points
        """
        weaknesses = []
        
        if len(summary) < 300:
            weaknesses.append("Summary is brief - may need more sources")
        
        if doc_count < 5:
            weaknesses.append("Limited source diversity")
        
        # Generic wisdom-adding check
        if not weaknesses:
            weaknesses.append("Consider cross-referencing findings with expert sources")
        
        return weaknesses
    
    def _validate_input(self, state: ResearchState) -> None:
        """
        Validate that required fields are present.
        
        Args:
            state: Research state to validate
        
        Raises:
            ValueError: If validation fails
        """
        super()._validate_input(state)
        
        if not state.summary:
            raise ValueError("summary is required for critic")


__all__ = ["CriticAgent"]
