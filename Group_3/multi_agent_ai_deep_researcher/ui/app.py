"""
Streamlit UI for Multi-Agent AI Deep Researcher.

Main interface featuring:
- Research query input with configuration
- Real-time streaming of agent outputs
- Session management and resumption
- Source citation and report visualization
"""

import sys
import os
import streamlit as st
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import utils, agents, main
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.state import ResearchState
    from main import build_research_graph
    from config import settings
except ImportError as e:
    st.error(f"❌ Import Error: {str(e)}")
    st.stop()


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="🔬 AI Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.5em;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    .step-complete {
        color: #28a745;
        font-weight: bold;
    }
    .step-active {
        color: #ffc107;
        font-weight: bold;
    }
    .step-pending {
        color: #6c757d;
    }
    .source-badge {
        display: inline-block;
        background: #e9ecef;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.markdown("## ⚙️ Configuration")

# API Key Input
api_key = st.sidebar.text_input(
    "Tavily API Key",
    type="password",
    help="Get your free key from https://tavily.com"
)

if api_key:
    # Apply key for current process/run
    st.session_state.tavily_api_key = api_key
    settings.tavily_api_key = api_key
    os.environ["TAVILY_API_KEY"] = api_key

# Session Management
st.sidebar.markdown("## 📋 Sessions")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.created_at = datetime.now()

st.sidebar.info(
    f"**Current Session**\n\n"
    f"ID: `{st.session_state.session_id[:12]}...`\n\n"
    f"Created: {st.session_state.created_at.strftime('%Y-%m-%d %H:%M')}"
)

# New Session Button
if st.sidebar.button("🔄 New Session", use_container_width=True):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.created_at = datetime.now()
    st.session_state.clear()
    st.rerun()

# ============================================================================
# MAIN INTERFACE
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<p class="main-title">🔬 AI Deep Researcher</p>', unsafe_allow_html=True)

st.markdown("*Autonomous research powered by LangGraph + Ollama + Tavily*")

# ============================================================================
# TABS: INPUT / RESULTS / SOURCES / HISTORY
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research", "📊 Results", "📚 Sources", "⏱️ History"])

# ============================================================================
# TAB 1: RESEARCH INPUT
# ============================================================================

with tab1:
    st.markdown("### Enter Your Research Query")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Research Question",
            placeholder="What are the latest developments in AI safety?",
            height=100,
            help="Enter a detailed research question or topic"
        )
    
    with col2:
        st.markdown("### Settings")
        max_sources = st.slider(
            "Max Sources",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of web sources to retrieve"
        )
        
        max_refinement = st.slider(
            "Max Refinement Passes",
            min_value=1,
            max_value=3,
            value=2,
            help="Maximum iterations for research refinement"
        )
    
    # Research Button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        research_button = st.button(
            "🚀 Start Research",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        clear_button = st.button(
            "🗑️ Clear",
            use_container_width=True
        )
    
    if clear_button:
        st.session_state.clear()
        st.rerun()
    
    # Execute Research
    if research_button and query:
        # Initialize session state for results
        st.session_state.is_researching = True
        st.session_state.query = query
        st.session_state.results = None
        
        # Build graph
        research_graph = build_research_graph(max_sources=max_sources)
        
        # Progress display
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 📈 Research Progress")
            
            # Step indicators
            cols = st.columns(5)
            steps = [
                ("🔍", "Retriever", "Gathering sources"),
                ("📝", "Summarizer", "Condensing findings"),
                ("✓", "Critic", "Quality assessment"),
                ("💡", "Insight", "Extracting key insights"),
                ("📄", "Reporter", "Generating report"),
            ]
            
            status_containers = []
            for col, (icon, name, desc) in zip(cols, steps):
                with col:
                    status_containers.append(st.empty())
                    status_containers[-1].markdown(
                        f"<p class='step-pending'>{icon} {name}</p><small>{desc}</small>",
                        unsafe_allow_html=True
                    )
            
            # Initialize state
            state = ResearchState(
                user_query=query,
                session_id=st.session_state.session_id,
                current_step="init",
                iteration_count=0,
                total_iterations=max_refinement,
            )
            
            # Run research with streaming
            config = {"configurable": {"thread_id": st.session_state.session_id}}
            
            current_step_index = 0
            
            try:
                # Stream updates from graph
                for output in research_graph.stream(
                    state.to_dict(),
                    config=config,
                    stream_mode="updates",
                ):
                    for node, values in output.items():
                        if node != "__start__":
                            # Update step indicator
                            step_map = {
                                "retriever": 0,
                                "summarizer": 1,
                                "critic": 2,
                                "insight": 3,
                                "reporter": 4,
                            }
                            
                            if node in step_map:
                                idx = step_map[node]
                                icon, name, _ = steps[idx]
                                status_containers[idx].markdown(
                                    f"<p class='step-active'>{icon} {name} ✓</p>",
                                    unsafe_allow_html=True
                                )
                
                # Get final state
                final_state = research_graph.get_state(config)
                if final_state:
                    st.session_state.results = final_state.values
                    st.success("✅ Research complete!")
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Research failed: {str(e)}")

# ============================================================================
# TAB 2: RESULTS
# ============================================================================

with tab2:
    if st.session_state.get("results"):
        results = st.session_state.results
        
        # Summary Section
        if results.get("summary"):
            with st.expander("📝 Summary", expanded=True):
                st.markdown(results["summary"])
        
        # Critique Section
        if results.get("critique"):
            critique = results["critique"]
            with st.expander("✓ Quality Assessment"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Coverage Score",
                        f"{critique.get('coverage_score', 0):.1%}"
                    )
                
                with col2:
                    needs_refine = critique.get("needs_refinement", False)
                    st.metric(
                        "Quality",
                        "🟢 Adequate" if not needs_refine else "🟡 Needs refinement"
                    )
                
                with col3:
                    st.metric(
                        "Flagged Sources",
                        len(critique.get("sources_flagged", []))
                    )
                
                if critique.get("strengths"):
                    st.markdown("**Strengths:**")
                    for strength in critique["strengths"]:
                        st.write(f"✓ {strength}")
                
                if critique.get("weaknesses"):
                    st.markdown("**Areas for Improvement:**")
                    for weakness in critique["weaknesses"]:
                        st.write(f"⚠️ {weakness}")
        
        # Insights Section
        if results.get("insights"):
            with st.expander("💡 Key Insights", expanded=True):
                for i, insight in enumerate(results["insights"], 1):
                    confidence = insight.get("confidence", 0.7)
                    confidence_bars = "█" * int(confidence * 5) + "░" * (5 - int(confidence * 5))
                    
                    st.markdown(f"**Insight {i}**")
                    st.write(insight.get("text", ""))
                    st.caption(f"Confidence: {confidence_bars} {confidence:.0%}")
        
        # Final Report Section
        if results.get("final_report"):
            with st.expander("📄 Full Report", expanded=False):
                st.markdown(results["final_report"])
                
                # Export buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Markdown",
                        data=results["final_report"],
                        file_name=f"research_{st.session_state.session_id[:8]}.md",
                        mime="text/markdown"
                    )
    else:
        st.info("👈 Start a research query to see results here")

# ============================================================================
# TAB 3: SOURCES
# ============================================================================

with tab3:
    if st.session_state.get("results") and st.session_state.results.get("source_metadata"):
        sources = st.session_state.results["source_metadata"]
        
        st.markdown(f"### 📚 {len(sources)} Sources Found")
        
        # Create source table
        source_data = []
        for doc_id, metadata in sources.items():
            source_data.append({
                "Title": metadata.get("title", "")[:60],
                "Domain": metadata.get("domain", ""),
                "Confidence": f"{metadata.get('confidence', 0.5):.0%}",
                "URL": metadata.get("url", ""),
            })
        
        st.dataframe(
            source_data,
            use_container_width=True,
            hide_index=True,
        )
        
        # Source breakdown by domain
        domains = {}
        for _, metadata in sources.items():
            domain = metadata.get("domain", "Unknown")
            domains[domain] = domains.get(domain, 0) + 1
        
        if domains:
            st.markdown("### Domain Breakdown")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.bar_chart(domains)
            
            with col2:
                st.write("**Domain Count:**")
                for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {domain}: **{count}** sources")
    else:
        st.info("👈 Complete research to see sources here")

# ============================================================================
# TAB 4: SESSION HISTORY
# ============================================================================

with tab4:
    st.markdown("### Session Information")
    
    if st.session_state.get("results"):
        metadata = st.session_state.results.get("execution_metadata", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Sources", st.session_state.results.get("total_sources_used", 0))
        
        with col2:
            iterations = st.session_state.results.get("iteration_count", 0)
            st.metric("Iterations", iterations)
        
        with col3:
            st.metric(
                "Timestamp",
                st.session_state.results.get("report_generated_at", "N/A")[:10]
            )
        
        st.markdown("### Agent Execution Times")
        
        if metadata:
            times_dict = {
                k.replace("_duration_ms", ""): v
                for k, v in metadata.items()
                if "duration_ms" in k
            }
            
            if times_dict:
                st.bar_chart(times_dict)
    else:
        st.info("No research completed yet")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

footer_cols = st.columns([1, 1, 1])

with footer_cols[0]:
    st.caption("🔬 Multi-Agent AI Deep Researcher")

with footer_cols[1]:
    st.caption("Phase 2 Complete - Phase 4: UI in Progress")

with footer_cols[2]:
    st.caption("Powered by LangGraph + Ollama + Tavily")
