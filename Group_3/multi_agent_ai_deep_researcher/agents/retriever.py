"""
Retriever Agent for the Multi-Agent AI Deep Researcher.

This is a RAG (Retrieval-Augmented Generation) agent that:
1. Takes a user query
2. Searches for relevant sources using Tavily API
3. Scrapes and extracts content from relevant URLs
4. Tracks source metadata (URL, title, confidence, timestamp)
5. Returns structured documents for downstream analysis

The Retriever is the first agent in the pipeline and provides the raw data
that other agents (Summarizer, Critic, Insight, Reporter) will process.

Design:
- Multi-source retrieval (combines multiple search results)
- Metadata tracking for source credibility and citations
- Error recovery (gracefully handles failed scrapes)
- Logging for debugging and performance tracking
"""

import hashlib
from typing import List, Dict, Any
from tavily import TavilyClient

from agents.base import BaseAgent
from config import settings
from utils.state import ResearchState, StateUpdate, SourceMetadata
from utils.scraper import scrape_url


class RetrieverAgent(BaseAgent):
    """
    Retrieval agent for searching and scraping relevant sources.
    
    This agent:
    1. Performs web search using Tavily API
    2. Scrapes and extracts content from search results
    3. Tracks source metadata for citations
    4. Handles errors gracefully (continues on failed scrapes)
    
    Attributes:
        max_sources: Maximum number of sources to retrieve
        scrape_timeout: Timeout for scraping individual URLs
    """
    
    def __init__(
        self,
        max_sources: int = 10,
        scrape_timeout: int = 10,
    ):
        """
        Initialize the Retriever Agent.
        
        Args:
            max_sources: Maximum number of sources to return
            scrape_timeout: Timeout for scraping each URL in seconds
        """
        super().__init__("retriever")
        self.max_sources = max_sources
        self.scrape_timeout = scrape_timeout
        self.tavily_client = TavilyClient(api_key=settings.tavily_api_key)
    
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute retrieval for the given query.
        
        Args:
            state: Current research state
        
        Returns:
            State update with retrieved documents and source metadata
        """
        session_id = state.session_id
        user_query = state.user_query
        iteration = state.iteration_count
        
        if not user_query:
            error = "No user query provided"
            return {
                "retrieved_docs": [],
                "source_metadata": {},
                "error_messages": [error],
                "current_step": "retriever",
            }
        
        try:
            # Perform search
            search_results = self._search(user_query, iteration)
            
            # Scrape and extract content from results
            documents, source_metadata = self._scrape_results(
                search_results,
                session_id,
                iteration,
            )
            
            # Convert SourceMetadata objects to dicts for state update
            source_metadata_dicts = {
                k: v.model_dump() if isinstance(v, SourceMetadata) else v
                for k, v in source_metadata.items()
            }
            
            return {
                "retrieved_docs": documents,
                "source_metadata": source_metadata_dicts,
                "current_step": "retriever",
                "iteration_count": iteration + 1,
            }
            
        except Exception as e:
            error_msg = f"Retriever agent failed: {str(e)}"
            return {
                "retrieved_docs": [],
                "source_metadata": {},
                "error_messages": [error_msg],
                "current_step": "retriever",
            }
    
    def _search(self, query: str, iteration: int = 0) -> List[Dict[str, str]]:
        """
        Perform web search using Tavily API.
        
        Args:
            query: Search query
            iteration: Iteration number (unused but kept for consistency)
        
        Returns:
            List of search results with 'title', 'url', 'snippet' keys
        """
        try:
            response = self.tavily_client.search(
                query=query,
                max_results=self.max_sources,
                include_answer=False,
            )
            
            # Convert to consistent format
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                })
            
            return results
            
        except Exception as e:
            return []
    
    def _scrape_results(
        self,
        search_results: List[Dict[str, str]],
        session_id: str,
        iteration: int,
    ) -> tuple[List[str], Dict[str, SourceMetadata]]:
        """
        Scrape content from search results.
        
        Handles errors gracefully - skips failed scrapes and continues.
        
        Args:
            search_results: List of search results from Tavily
            session_id: Session ID for logging
            iteration: Current iteration number
        
        Returns:
            Tuple of (documents list, source_metadata dict with SourceMetadata objects)
        """
        documents = []
        source_metadata: Dict[str, SourceMetadata] = {}
        
        for idx, result in enumerate(search_results):
            url = result.get("url", "")
            if not url:
                continue
            
            try:
                scrape_result = scrape_url(url, timeout=self.scrape_timeout)
                
                if not scrape_result.success:
                    continue
                
                # Extract content
                content = scrape_result.content
                if not content or len(content) < 50:
                    continue
                
                # Create document ID
                doc_id = self._create_doc_id(url)
                
                # Store document
                documents.append(content)
                
                # Create SourceMetadata object
                metadata = SourceMetadata(
                    url=url,
                    title=result.get("title", scrape_result.title),
                    snippet=result.get("snippet", ""),
                    excerpt=content[:200],  # First 200 chars as excerpt
                    confidence=self._calculate_confidence(scrape_result),
                    domain=self._extract_domain(url),
                    author=scrape_result.metadata.author,
                )
                
                source_metadata[doc_id] = metadata
                
            except Exception as e:
                # Continue with next result instead of failing
                continue
        
        return documents, source_metadata
    
    def _create_doc_id(self, url: str) -> str:
        """
        Create unique document ID from URL.
        
        Args:
            url: Source URL
        
        Returns:
            Document ID as hash
        """
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: Full URL
        
        Returns:
            Domain name (e.g., "example.com")
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
    
    def _calculate_confidence(self, scrape_result: Any) -> float:
        """
        Calculate confidence score for scraped content.
        
        Higher score = more reliable source.
        Factors: content length, metadata availability, successful scrape.
        
        Args:
            scrape_result: Result from scraper
        
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Boost for successful scrape
        if scrape_result.success:
            confidence += 0.2
        
        # Boost for longer content (more substantial article)
        content_len = len(scrape_result.content or "")
        if content_len > 1000:
            confidence += 0.15
        elif content_len > 500:
            confidence += 0.1
        
        # Boost for available metadata
        metadata = scrape_result.metadata
        if metadata.author:
            confidence += 0.1
        if metadata.published_date:
            confidence += 0.05
        
        return min(1.0, confidence)  # Cap at 1.0
    
    def _validate_input(self, state: ResearchState) -> None:
        """
        Validate that required fields are present.
        
        Args:
            state: Research state to validate
        
        Raises:
            ValueError: If validation fails
        """
        super()._validate_input(state)
        
        if not state.user_query:
            raise ValueError("user_query is required for retriever")


__all__ = ["RetrieverAgent"]
