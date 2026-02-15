"""
Reusable Streamlit components for the UI.

Components include:
- Step progress indicator
- Streaming output display
- Source citation viewer
- Confidence visualizations
- Session history display
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime


def display_step_progress(
    current_step: str,
    steps: List[tuple] = None,
    container = None
) -> None:
    """
    Display progress through research steps.
    
    Args:
        current_step: Current step name
        steps: List of (icon, name, description) tuples
        container: Streamlit container to use
    """
    if steps is None:
        steps = [
            ("🔍", "Retriever", "Gathering sources"),
            ("📝", "Summarizer", "Condensing findings"),
            ("✓", "Critic", "Quality assessment"),
            ("💡", "Insight", "Extracting insights"),
            ("📄", "Reporter", "Generating report"),
        ]
    
    if container is None:
        container = st
    
    step_map = {step[1].lower(): i for i, step in enumerate(steps)}
    current_idx = step_map.get(current_step.lower(), -1)
    
    cols = container.columns(len(steps))
    
    for idx, (col, (icon, name, desc)) in enumerate(zip(cols, steps)):
        with col:
            if idx < current_idx:
                # Completed
                st.markdown(f"<p style='color: #28a745;'>✅ {name}</p>", unsafe_allow_html=True)
            elif idx == current_idx:
                # Active
                st.markdown(f"<p style='color: #ffc107;'>🔄 {name}</p>", unsafe_allow_html=True)
            else:
                # Pending
                st.markdown(f"<p style='color: #6c757d;'>{icon} {name}</p>", unsafe_allow_html=True)


def display_source_with_confidence(
    url: str,
    title: str,
    confidence: float,
    domain: str = None,
    author: str = None,
    container = None
) -> None:
    """
    Display source with confidence badge and metadata.
    
    Args:
        url: Source URL
        title: Article title
        confidence: Confidence score (0-1)
        domain: Source domain
        author: Article author
        container: Streamlit container to use
    """
    if container is None:
        container = st
    
    # Confidence rating
    if confidence >= 0.8:
        rating = "⭐⭐⭐ High"
        color = "#28a745"
    elif confidence >= 0.6:
        rating = "⭐⭐ Medium"
        color = "#ffc107"
    else:
        rating = "⭐ Low"
        color = "#dc3545"
    
    # Confidence bar
    bars = "█" * int(confidence * 5) + "░" * (5 - int(confidence * 5))
    
    # Display
    container.markdown(
        f"**{title}**\n\n"
        f"🔗 [{domain}]({url})\n\n"
        f"**Confidence:** {bars} {confidence:.0%}  /  {rating}\n\n"
        + (f"**Author:** {author}\n\n" if author else ""),
        unsafe_allow_html=True
    )


def display_insight_with_confidence(
    text: str,
    confidence: float,
    supporting_sources: List[str] = None,
    reasoning: str = None,
    container = None
) -> None:
    """
    Display insight with confidence visualization.
    
    Args:
        text: Insight text
        confidence: Confidence score (0-1)
        supporting_sources: List of supporting source URLs
        reasoning: Reasoning behind insight
        container: Streamlit container to use
    """
    if container is None:
        container = st
    
    # Confidence bar
    bars = "█" * int(confidence * 5) + "░" * (5 - int(confidence * 5))
    
    # Main insight
    container.markdown(
        f"**💡 {text}**\n\n"
        f"**Confidence:** {bars} {confidence:.0%}"
    )
    
    # Reasoning if provided
    if reasoning:
        container.caption(f"*Reasoning: {reasoning}*")
    
    # Sources if provided
    if supporting_sources:
        with container.expander("📚 Supporting Sources"):
            for i, source in enumerate(supporting_sources[:3], 1):
                st.write(f"{i}. {source[:80]}...")


def display_execution_metadata(
    metadata: Dict[str, Any],
    container = None
) -> None:
    """
    Display agent execution metadata.
    
    Args:
        metadata: Execution metadata dict
        container: Streamlit container to use
    """
    if container is None:
        container = st
    
    col1, col2, col3 = container.columns(3)
    
    # Extract metrics
    retriever_time = metadata.get("retriever_duration_ms", 0)
    summarizer_time = metadata.get("summarizer_duration_ms", 0)
    critic_time = metadata.get("critic_duration_ms", 0)
    insight_time = metadata.get("insight_duration_ms", 0)
    reporter_time = metadata.get("reporter_duration_ms", 0)
    
    total_time = sum([retriever_time, summarizer_time, critic_time, insight_time, reporter_time])
    
    with col1:
        col1.metric("Total Time", f"{total_time / 1000:.1f}s")
    
    with col2:
        avg_time = total_time / 5 if total_time > 0 else 0
        col2.metric("Avg Agent Time", f"{avg_time / 1000:.1f}s")
    
    with col3:
        col3.metric("Agents Run", "5")
    
    # Timeline
    container.markdown("### Execution Timeline")
    
    times_data = {
        "Retriever": retriever_time / 1000,
        "Summarizer": summarizer_time / 1000,
        "Critic": critic_time / 1000,
        "Insight": insight_time / 1000,
        "Reporter": reporter_time / 1000,
    }
    
    container.bar_chart(times_data)


def display_session_history(
    sessions: List[Dict[str, Any]],
    container = None,
) -> Optional[str]:
    """
    Display session history with resume options.
    
    Args:
        sessions: List of session metadata dicts
        container: Streamlit container to use
    
    Returns:
        Selected session ID or None
    """
    if container is None:
        container = st
    
    if not sessions:
        container.info("No previous sessions")
        return None
    
    container.markdown("### Previous Sessions")
    
    selected_session = None
    
    for session in sessions[:10]:  # Show last 10 sessions
        col1, col2, col3 = container.columns([3, 1, 1])
        
        with col1:
            query = session.get("query", "")[:60]
            created = session.get("created_at", "")
            col1.markdown(f"**{query}...**\n\n*{created}*")
        
        with col2:
            sources = session.get("total_sources", 0)
            col2.metric("Sources", sources)
        
        with col3:
            if col3.button("Resume", key=session["session_id"]):
                selected_session = session["session_id"]
    
    return selected_session


def display_report_export_buttons(
    report_content: str,
    session_id: str,
    container = None
) -> None:
    """
    Display export buttons for report.
    
    Args:
        report_content: Report markdown content
        session_id: Session identifier
        container: Streamlit container to use
    """
    if container is None:
        container = st
    
    col1, col2, col3 = container.columns(3)
    
    with col1:
        col1.download_button(
            label="📥 Markdown",
            data=report_content,
            file_name=f"research_{session_id[:8]}.md",
            mime="text/markdown"
        )
    
    with col2:
        # Create simple HTML version
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Research Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; }}
                h1 {{ color: #333; border-bottom: 2px solid #667eea; }}
                h2 {{ color: #667eea; margin-top: 2em; }}
                code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
                pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
        {report_content}
        </body>
        </html>
        """
        
        col2.download_button(
            label="📄 HTML",
            data=html_content,
            file_name=f"research_{session_id[:8]}.html",
            mime="text/html"
        )
    
    with col3:
        col3.write("📋 PDF support coming soon")


def display_confidence_badge(
    value: float,
    label: str = None,
    container = None
) -> None:
    """
    Display a confidence badge.
    
    Args:
        value: Confidence value (0-1)
        label: Optional label text
        container: Streamlit container to use
    """
    if container is None:
        container = st
    
    if value >= 0.8:
        color = "#28a745"  # Green
        text = "High"
    elif value >= 0.6:
        color = "#ffc107"  # Yellow
        text = "Medium"
    else:
        color = "#dc3545"  # Red
        text = "Low"
    
    bars = "█" * int(value * 5) + "░" * (5 - int(value * 5))
    
    badge = f"<span style='background: {color}; color: white; padding: 4px 8px; border-radius: 4px;'>{bars} {value:.0%} ({text})</span>"
    
    if label:
        container.markdown(f"**{label}:** {badge}", unsafe_allow_html=True)
    else:
        container.markdown(badge, unsafe_allow_html=True)


__all__ = [
    "display_step_progress",
    "display_source_with_confidence",
    "display_insight_with_confidence",
    "display_execution_metadata",
    "display_session_history",
    "display_report_export_buttons",
    "display_confidence_badge",
]
