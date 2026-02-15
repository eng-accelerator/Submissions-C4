"""
Summarizer Agent for the Multi-Agent AI Deep Researcher.

This agent:
1. Takes retrieved documents
2. Condenses them into a coherent summary
3. Extracts key points and themes
4. Returns structured summary for downstream analysis
"""

from typing import Dict, Any
from utils.state import ResearchState, StateUpdate
from utils.llm import call_llm
from agents.base import BaseAgent


class SummarizerAgent(BaseAgent):
    """
    Summarization agent for condensing research findings.
    
    This agent:
    1. Condenses multiple documents into coherent summary
    2. Extracts key themes and insights
    3. Maintains source attribution
    """
    
    def __init__(self, max_summary_length: int = 1000):
        """
        Initialize the Summarizer Agent.
        
        Args:
            max_summary_length: Maximum length of summary in characters
        """
        super().__init__("summarizer")
        self.max_summary_length = max_summary_length
    
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute summarization on retrieved documents.
        
        Args:
            state: Current research state with retrieved_docs
        
        Returns:
            State update with summary and key points
        """
        session_id = state.session_id
        user_query = state.user_query
        documents = state.retrieved_docs
        
        if not documents:
            return {
                "summary": "",
                "current_step": "summarizer",
                "error_messages": ["No documents available for summarization"],
            }
        
        try:
            # Combine documents with truncation if needed
            combined_docs = "\n\n---\n\n".join(documents[:10])[:5000]
            
            # Create summarization prompt
            prompt = f"""Based on the following research documents about "{user_query}", 
provide a concise summary highlighting the key findings and themes (max {self.max_summary_length} chars):

DOCUMENTS:
{combined_docs}

SUMMARY:"""
            
            # Call LLM for summarization
            llm_response = call_llm(
                prompt,
                max_tokens=500,
                temperature=0.3  # Lower temp for more focused summary
            )
            
            if llm_response.get("success"):
                summary = llm_response.get("content", "").strip()[:self.max_summary_length]
                
                return {
                    "summary": summary,
                    "current_step": "summarizer",
                    "execution_metadata": {
                        "summarizer_tokens_input": llm_response.get("input_tokens", 0),
                        "summarizer_tokens_output": llm_response.get("output_tokens", 0),
                    },
                }
            else:
                error = f"LLM error: {llm_response.get('error', 'unknown')}"
                return {
                    "summary": "",
                    "current_step": "summarizer",
                    "error_messages": [error],
                }
        
        except Exception as e:
            error_msg = f"Summarizer agent failed: {str(e)}"
            return {
                "summary": "",
                "current_step": "summarizer",
                "error_messages": [error_msg],
            }
    
    def _validate_input(self, state: ResearchState) -> None:
        """
        Validate that required fields are present.
        
        Args:
            state: Research state to validate
        
        Raises:
            ValueError: If validation fails
        """
        super()._validate_input(state)
        
        if not state.retrieved_docs:
            raise ValueError("retrieved_docs are required for summarizer")


__all__ = ["SummarizerAgent"]
