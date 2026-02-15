"""
Reporter Agent for the Multi-Agent AI Deep Researcher.

This agent:
1. Takes all the analysis from previous agents (summary, critique, insights)
2. Generates a structured markdown report
3. Includes source citations with confidence indicators
4. Produces professional, actionable output
5. Supports streaming of report sections

The Reporter is the final agent in the pipeline that compiles all insights
into a single coherent, well-formatted research report.

Report structure:
- Title/Executive Summary
- Key Findings (from summary)
- Source Analysis (credibility assessment)
- Insights & Hypotheses (with confidence scores)
- Recommendations
- References
"""

from datetime import datetime
from typing import Dict, Any
from io import StringIO

from agents.base import BaseAgent
from utils.state import ResearchState, StateUpdate, SourceMetadata, Insight
from utils.llm import call_llm, stream_llm, count_tokens


class ReporterAgent(BaseAgent):
    """
    Report generation agent that compiles research findings into structured output.
    
    This agent:
    1. Takes summary, critique, and insights from other agents
    2. Generates a professional markdown report
    3. Includes source citations with confidence metrics
    4. Supports streaming of report sections for real-time UI updates
    
    Attributes:
        max_report_length: Maximum length of final report
        enable_streaming: Whether to stream sections for real-time display
    """
    
    def __init__(self, max_report_length: int = 10000, enable_streaming: bool = True):
        """
        Initialize the Reporter Agent.
        
        Args:
            max_report_length: Maximum report length in characters
            enable_streaming: Enable streaming of report sections
        """
        super().__init__("reporter")
        self.max_report_length = max_report_length
        self.enable_streaming = enable_streaming
    
    def execute(self, state: ResearchState) -> StateUpdate:
        """
        Execute report generation.
        
        Args:
            state: Current research state with all analysis results
        
        Returns:
            State update with generated report
        """
        session_id = state.session_id
        
        try:
            # Generate report sections
            report_sections = self._generate_report_sections(state)
            
            # Combine into final report
            final_report = self._compile_report(report_sections, state)
            
            # Count sources used
            sources_used = len(state.source_metadata)
            
            return {
                "final_report": final_report,
                "total_sources_used": sources_used,
                "report_generated_at": datetime.utcnow().isoformat(),
                "current_step": "reporter",
            }
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            return {
                "error_messages": [error_msg],
                "current_step": "reporter",
                "final_report": self._generate_fallback_report(state),
            }
    
    def _generate_report_sections(self, state: ResearchState) -> Dict[str, str]:
        """
        Generate individual report sections.
        
        Args:
            state: Research state with all analysis
        
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        
        # 1. Title and Executive Summary
        sections["title"] = self._generate_title(state)
        sections["executive_summary"] = self._generate_executive_summary(state)
        
        # 2. Key Findings
        sections["key_findings"] = self._generate_key_findings(state)
        
        # 3. Source Analysis
        sections["source_analysis"] = self._generate_source_analysis(state)
        
        # 4. Detailed Analysis
        sections["detailed_analysis"] = self._generate_detailed_analysis(state)
        
        # 5. Insights & Hypotheses
        sections["insights"] = self._generate_insights_section(state)
        
        # 6. Recommendations
        sections["recommendations"] = self._generate_recommendations(state)
        
        # 7. References
        sections["references"] = self._generate_references(state)
        
        return sections
    
    def _generate_title(self, state: ResearchState) -> str:
        """Generate report title from query."""
        query = state.user_query
        return f"# Research Report: {query}\n"
    
    def _generate_executive_summary(self, state: ResearchState) -> str:
        """Generate executive summary from summary field."""
        summary = state.summary or ""
        if not summary:
            return ""
        
        return f"""## Executive Summary

{summary}

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Sources Analyzed:** {len(state.source_metadata)}

"""
    
    def _generate_key_findings(self, state: ResearchState) -> str:
        """Generate key findings section."""
        findings = StringIO()
        findings.write("## Key Findings\n\n")
        
        # Extract findings from summary
        summary = state.summary or ""
        if summary:
            # Simple heuristic: first 2-3 sentences are key findings
            sentences = summary.split(". ")[:3]
            findings.write("### Main Points\n\n")
            for i, sentence in enumerate(sentences, 1):
                if sentence.strip():
                    findings.write(f"{i}. {sentence.strip()}.\n")
            findings.write("\n")
        
        # Add critique findings
        critique = state.critique
        if critique.strengths:
            findings.write("### Strengths\n\n")
            for strength in critique.strengths[:3]:
                findings.write(f"- {strength}\n")
            findings.write("\n")
        
        if critique.weaknesses:
            findings.write("### Areas for Caution\n\n")
            for weakness in critique.weaknesses[:3]:
                findings.write(f"- {weakness}\n")
            findings.write("\n")
        
        return findings.getvalue()
    
    def _generate_source_analysis(self, state: ResearchState) -> str:
        """Generate source credibility analysis section."""
        analysis = StringIO()
        analysis.write("## Source Analysis\n\n")
        
        source_metadata = state.source_metadata
        if not source_metadata:
            analysis.write("*No sources available for analysis*\n\n")
            return analysis.getvalue()
        
        # Sort sources by confidence
        sorted_sources = sorted(
            source_metadata.items(),
            key=lambda x: x[1].confidence if isinstance(x[1], SourceMetadata) else x[1].get("confidence", 0.5),
            reverse=True
        )
        
        analysis.write("### Source Credibility Ratings\n\n")
        analysis.write("| Domain | Confidence | Title |\n")
        analysis.write("|--------|------------|-------|\n")
        
        for doc_id, metadata in sorted_sources[:10]:  # Top 10 sources
            if isinstance(metadata, SourceMetadata):
                domain = metadata.domain
                confidence = metadata.confidence
                title = metadata.title[:50]
            else:
                domain = metadata.get("domain", "unknown")
                confidence = metadata.get("confidence", 0.5)
                title = metadata.get("title", "Untitled")[:50]
            
            # Convert confidence to rating
            if confidence >= 0.8:
                rating = "⭐⭐⭐ High"
            elif confidence >= 0.6:
                rating = "⭐⭐ Medium"
            else:
                rating = "⭐ Low"
            
            analysis.write(f"| {domain} | {rating} | {title} |\n")
        
        analysis.write("\n")
        
        # Add data quality assessment
        critique = state.critique
        if critique.contradictions:
            analysis.write("### Notable Contradictions\n\n")
            for contradiction in critique.contradictions[:3]:
                analysis.write(f"- {contradiction}\n")
            analysis.write("\n")
        
        return analysis.getvalue()
    
    def _generate_detailed_analysis(self, state: ResearchState) -> str:
        """Generate detailed analysis section."""
        analysis = StringIO()
        analysis.write("## Detailed Analysis\n\n")
        
        summary = state.summary
        if summary:
            analysis.write(summary)
        else:
            analysis.write("*Detailed analysis data not available*\n")
        
        analysis.write("\n\n")
        return analysis.getvalue()
    
    def _generate_insights_section(self, state: ResearchState) -> str:
        """Generate insights and hypotheses section."""
        insights = StringIO()
        insights.write("## Insights & Hypotheses\n\n")
        
        state_insights = state.insights
        if not state_insights:
            insights.write("*No insights generated in this analysis*\n\n")
            return insights.getvalue()
        
        for idx, insight in enumerate(state_insights, 1):
            if isinstance(insight, Insight):
                text = insight.text
                confidence = insight.confidence
            elif isinstance(insight, dict):
                text = insight.get("text", "")
                confidence = insight.get("confidence", 0.5)
            else:
                text = str(insight)
                confidence = 0.5
            
            if not text:
                continue
            
            # Convert confidence to visual indicator
            confidence_bars = "█" * int(confidence * 5) + "░" * (5 - int(confidence * 5))
            
            insights.write(f"### Insight {idx}\n\n")
            insights.write(f"**Confidence:** {confidence_bars} ({confidence:.1%})\n\n")
            insights.write(f"{text}\n\n")
        
        return insights.getvalue()
    
    def _generate_recommendations(self, state: ResearchState) -> str:
        """Generate recommendations section."""
        recommendations = StringIO()
        recommendations.write("## Recommendations\n\n")
        
        critique = state.critique
        insights = state.insights
        
        if not insights:
            recommendations.write("1. Continue research to gather more insights\n")
        else:
            recommendations.write("Based on the analysis:\n\n")
            recommendations.write("1. **Further Investigation**: Areas identified in the analysis merit deeper exploration\n")
            recommendations.write("2. **Source Verification**: Verify conflicting information in multiple sources\n")
            recommendations.write("3. **Hypothesis Testing**: Validate generated hypotheses with domain experts\n")
        
        if critique.needs_refinement:
            recommendations.write("4. **Refinement Needed**: Additional research passes recommended for comprehensive coverage\n")
        
        recommendations.write("\n")
        return recommendations.getvalue()
    
    def _generate_references(self, state: ResearchState) -> str:
        """Generate references/citations section."""
        references = StringIO()
        references.write("## References\n\n")
        
        source_metadata = state.source_metadata
        if not source_metadata:
            references.write("*No sources available*\n\n")
            return references.getvalue()
        
        references.write("### Sources Used\n\n")
        
        for idx, (doc_id, metadata) in enumerate(source_metadata.items(), 1):
            if isinstance(metadata, SourceMetadata):
                url = metadata.url
                title = metadata.title
                timestamp = metadata.timestamp
                confidence = metadata.confidence
            else:
                url = metadata.get("url", "")
                title = metadata.get("title", "Untitled")
                timestamp = metadata.get("timestamp", "")
                confidence = metadata.get("confidence", 0.5)
            
            # Format as citation
            references.write(f"[{idx}] **{title}**\n")
            references.write(f"    URL: [{url}]({url})\n")
            references.write(f"    Confidence: {confidence:.0%}\n")
            if timestamp:
                references.write(f"    Retrieved: {timestamp}\n")
            references.write("\n")
        
        return references.getvalue()
    
    def _compile_report(
        self,
        sections: Dict[str, str],
        state: ResearchState
    ) -> str:
        """
        Compile all sections into final report.
        
        Args:
            sections: Dictionary of report sections
            state: Research state
        
        Returns:
            Complete markdown report
        """
        report_parts = [
            sections.get("title", ""),
            sections.get("executive_summary", ""),
            sections.get("key_findings", ""),
            sections.get("source_analysis", ""),
            sections.get("detailed_analysis", ""),
            sections.get("insights", ""),
            sections.get("recommendations", ""),
            sections.get("references", ""),
        ]
        
        # Join all sections
        report = "\n".join(part for part in report_parts if part)
        
        # Truncate if necessary
        if len(report) > self.max_report_length:
            report = report[:self.max_report_length] + "\n\n*[Report truncated]*"
        
        return report
    
    def _generate_fallback_report(self, state: ResearchState) -> str:
        """
        Generate minimal fallback report if generation fails.
        
        Args:
            state: Research state
        
        Returns:
            Basic report structure
        """
        query = state.user_query
        summary = state.summary or "Report generation encountered an error."
        sources = len(state.source_metadata)
        
        return f"""# Research Report: {query}

## Summary
{summary}

## Metadata
- Sources Analyzed: {sources}
- Report Generated: {datetime.utcnow().isoformat()}
- Status: Partial (some sections unavailable)

*Note: Please review the error messages for details on what failed during generation.*
"""


__all__ = ["ReporterAgent"]
