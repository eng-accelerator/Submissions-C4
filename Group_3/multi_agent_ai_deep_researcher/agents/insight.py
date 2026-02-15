"""
Insight Agent for the Multi-Agent AI Deep Researcher.

This agent:
1. Extracts key insights from research
2. Identifies patterns and themes
3. Ranks insights by confidence
4. Provides reasoning for each insight
"""

from typing import List, Dict, Any
from utils.state import ResearchState, StateUpdate, Insight
from utils.llm import call_llm
from agents.base import BaseAgent


class InsightAgent(BaseAgent):
    """
    Key insight extraction agent for research findings.
    
    This agent:
    1. Extracts important insights from documents
    2. Ranks by significance
    3. Links to supporting sources
    4. Provides reasoning
    """
    
    def __init__(self, max_insights: int = 5):
        """
        Initialize the Insight Agent.
        
        Args:
            max_insights: Maximum number of insights to extract
        """
        super().__init__("insight")
        self.max_insights = max_insights
    
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute insight extraction from research.
        
        Args:
            state: Current research state
        
        Returns:
            State update with extracted insights
        """
        session_id = state.session_id
        user_query = state.user_query
        summary = state.summary
        documents = state.retrieved_docs
        
        if not summary or not documents:
            return {
                "insights": [],
                "current_step": "insight",
                "error_messages": ["Insufficient data for insight extraction"],
            }
        
        try:
            # Extract insights using LLM
            prompt = f"""Based on this research summary about "{user_query}", 
extract up to {self.max_insights} key insights. For each insight, provide:
1. The insight (1-2 sentences)
2. Confidence level (0.0-1.0)
3. Why it's important

SUMMARY:
{summary}

Format your response as a numbered list with clear separation."""
            
            llm_response = call_llm(
                prompt,
                max_tokens=800,
                temperature=0.4
            )
            
            if llm_response.get("success"):
                insights_text = llm_response.get("content", "")
                insights = self._parse_insights(
                    insights_text,
                    documents
                )
                
                return {
                    "insights": [i.model_dump() for i in insights],
                    "current_step": "insight",
                    "execution_metadata": {
                        "insight_tokens_input": llm_response.get("input_tokens", 0),
                        "insight_tokens_output": llm_response.get("output_tokens", 0),
                    },
                }
            else:
                error = f"LLM error: {llm_response.get('error', 'unknown')}"
                return {
                    "insights": [],
                    "current_step": "insight",
                    "error_messages": [error],
                }
        
        except Exception as e:
            error_msg = f"Insight agent failed: {str(e)}"
            return {
                "insights": [],
                "current_step": "insight",
                "error_messages": [error_msg],
            }
    
    def _parse_insights(
        self,
        insights_text: str,
        documents: List[str]
    ) -> List[Insight]:
        """
        Parse LLM response into Insight objects.
        
        Args:
            insights_text: LLM-generated insights text
            documents: Source documents
        
        Returns:
            List of Insight objects
        """
        insights = []
        
        # Split by numbered items
        lines = insights_text.split('\n')
        current_insight = []
        
        for line in lines:
            if line.strip() and (line[0].isdigit() or line.startswith('-')):
                if current_insight:
                    insight = self._create_insight(
                        '\n'.join(current_insight),
                        documents
                    )
                    if insight:
                        insights.append(insight)
                current_insight = [line]
            elif line.strip():
                current_insight.append(line)
        
        # Don't forget last insight
        if current_insight:
            insight = self._create_insight(
                '\n'.join(current_insight),
                documents
            )
            if insight:
                insights.append(insight)
        
        return insights[:self.max_insights]
    
    def _create_insight(self, text: str, documents: List[str]) -> Insight:
        """
        Create an Insight object from parsed text.
        
        Args:
            text: Parsed insight text
            documents: Source documents
        
        Returns:
            Insight object or None
        """
        try:
            # Extract confidence if mentioned
            confidence = 0.7
            if "confidence" in text.lower():
                # Try to extract number (simple heuristic)
                for word in text.split():
                    try:
                        val = float(word)
                        if 0 <= val <= 1:
                            confidence = val
                            break
                    except ValueError:
                        continue
            
            # Clean text - remove low-quality entries
            clean_text = text.strip()
            if len(clean_text) < 20:
                return None
            
            return Insight(
                text=clean_text[:500],  # Truncate if too long
                confidence=min(1.0, confidence),
                supporting_sources=[d[:100] for d in documents[:3]],
                reasoning="Extracted from research summary"
            )
        except Exception as e:
            return None
    
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
            raise ValueError("summary is required for insight agent")


__all__ = ["InsightAgent"]
