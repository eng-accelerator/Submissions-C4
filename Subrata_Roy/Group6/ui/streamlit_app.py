"""
Streamlit UI for DevOps Incident Analysis Suite
"""

import streamlit as st
from orchestrator.state import IncidentAnalysisState
from orchestrator.graph import IncidentAnalysisOrchestrator
from agents.cookbook import CookbookAgent
from utils.llm_client import LLMClient
import traceback


# Page configuration
st.set_page_config(
    page_title="DevOps Incident Analysis Suite",
    page_icon="🚨",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        background-color: #D4EDDA;
        border-left: 5px solid #28A745;
        padding: 10px;
        margin: 10px 0;
    }
    .status-error {
        background-color: #F8D7DA;
        border-left: 5px solid #DC3545;
        padding: 10px;
        margin: 10px 0;
    }
    .status-warning {
        background-color: #FFF3CD;
        border-left: 5px solid #FFC107;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🚨 DevOps Incident Analysis Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Agent AI System for Automated Incident Response</div>', unsafe_allow_html=True)

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

st.sidebar.subheader("🤖 LLM Configuration")
openrouter_api_key = st.sidebar.text_input(
    "OpenRouter API Key",
    type="password",
    help="Your OpenRouter API key for LLM access"
)
llm_model = st.sidebar.selectbox(
    "LLM Model",
    ["openai/gpt-4o", "openai/gpt-4-turbo", "anthropic/claude-3.5-sonnet", "google/gemini-pro"],
    help="Select the LLM model to use"
)

st.sidebar.subheader("📢 Slack Configuration")
slack_webhook_url = st.sidebar.text_input(
    "Slack Webhook URL",
    type="password",
    help="Slack webhook URL for notifications"
)

st.sidebar.subheader("🎫 JIRA Configuration")
jira_url = st.sidebar.text_input(
    "JIRA URL",
    placeholder="https://your-domain.atlassian.net",
    help="Your JIRA instance URL"
)
jira_username = st.sidebar.text_input(
    "JIRA Username/Email",
    help="Your JIRA username or email"
)
jira_api_token = st.sidebar.text_input(
    "JIRA API Token",
    type="password",
    help="Your JIRA API token"
)
jira_project_key = st.sidebar.text_input(
    "JIRA Project Key",
    placeholder="OPS",
    help="JIRA project key where tickets will be created (e.g., OPS, DEV, PROJ). Must exist in your JIRA instance."
)
jira_issue_type = st.sidebar.text_input(
    "JIRA Issue Type",
    value="Task",
    placeholder="Task",
    help="Issue type for created tickets (e.g., Task, Bug, Incident). Must exist in your JIRA project."
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Architecture:**
- 5 Specialized Agents
- LangGraph Orchestration
- RAG-style Reasoning
- Automated Workflow
""")

# Main content area
tab1, tab2 = st.tabs(["📊 Analyze Incident", "📖 About"])

with tab1:
    # Log input
    st.subheader("📝 Log Input")
    log_input = st.text_area(
        "Paste your application/system logs here:",
        height=200,
        placeholder="""Example:
2024-02-14 10:23:45 ERROR [payment-service] Database connection timeout after 30s
Connection pool exhausted: max_connections=100, active=100, idle=0
Error code: DB_CONN_TIMEOUT_001
Failed to process payment transaction for order #12345
""",
        help="Paste structured or semi-structured logs from your application"
    )
    
    # Sample logs button
    if st.button("📋 Load Sample Log"):
        log_input = """2024-02-14 10:23:45 CRITICAL [payment-service] Database connection timeout after 30s
Connection pool exhausted: max_connections=100, active=100, idle=0
Error code: DB_CONN_TIMEOUT_001
Failed to process payment transaction for order #12345
Stack trace: at com.payment.db.ConnectionPool.getConnection(ConnectionPool.java:145)"""
        st.rerun()
    
    # Analyze button
    analyze_button = st.button("🔍 Analyze Incident", type="primary", use_container_width=True)
    
    if analyze_button:
        # Validation
        if not openrouter_api_key:
            st.error("⚠️ Please provide OpenRouter API Key in the sidebar")
        elif not log_input.strip():
            st.error("⚠️ Please provide log input")
        else:
            try:
                with st.spinner("🤖 Multi-Agent Analysis in Progress..."):
                    # Create initial state
                    state = IncidentAnalysisState(
                        raw_log_input=log_input,
                        openrouter_api_key=openrouter_api_key,
                        tavily_api_key="",  # Not used in current implementation
                        slack_webhook_url=slack_webhook_url,
                        jira_url=jira_url,
                        jira_username=jira_username,
                        jira_api_token=jira_api_token,
                        jira_project_key=(jira_project_key or "OPS").strip(),
                        jira_issue_type=(jira_issue_type or "Task").strip(),
                        llm_model=llm_model
                    )
                    
                    # Create and run orchestrator
                    orchestrator = IncidentAnalysisOrchestrator(state)
                    final_state = orchestrator.run()
                    
                    # Check if final_state is valid
                    if final_state is None:
                        st.error("❌ Analysis failed: No state returned from orchestrator")
                        st.stop()

                    # Display results
                    st.success("✅ Analysis Complete!")
                    
                    # Show errors if any
                    if final_state.errors:
                        st.warning("⚠️ Some issues occurred during processing:")
                        for error in final_state.errors:
                            st.error(final_state.errors)
                    
                    # Display results in sections
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Classified Incident
                        st.subheader("🔍 Classified Incident")
                        if final_state.classified_incident:
                            incident = final_state.classified_incident
                            
                            # Severity badge
                            severity_colors = {
                                "INFO": "🔵",
                                "WARNING": "🟡",
                                "ERROR": "🟠",
                                "CRITICAL": "🔴"
                            }
                            st.markdown(f"**Severity:** {severity_colors.get(incident.severity, '⚪')} {incident.severity}")
                            st.markdown(f"**Type:** {incident.incident_type}")
                            st.markdown(f"**Service:** {incident.affected_service}")
                            st.markdown(f"**Summary:** {incident.summary}")
                            
                            with st.expander("Technical Details"):
                                st.write(incident.technical_details)
                        
                        # JIRA Ticket Status
                        st.subheader("🎫 JIRA Ticket Status")
                        if final_state.jira_ticket_status:
                            jira = final_state.jira_ticket_status
                            if jira.created:
                                st.markdown(f'<div class="status-success">✅ Ticket Created: <a href="{jira.ticket_url}" target="_blank">{jira.ticket_key}</a></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="status-warning">ℹ️ {jira.error or "Not created (non-critical incident)"}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        # Remediation Plan
                        st.subheader("🔧 Remediation Plan")
                        if final_state.remediation_plan:
                            remediation = final_state.remediation_plan
                            
                            st.markdown(f"**Urgency:** {remediation.urgency}")
                            st.markdown(f"**Root Cause:** {remediation.root_cause_hypothesis}")
                            
                            st.markdown("**Recommended Fixes:**")
                            for i, fix in enumerate(remediation.recommended_fixes, 1):
                                st.markdown(f"{i}. {fix}")
                            
                            with st.expander("Technical Rationale"):
                                st.write(remediation.technical_rationale)
                            
                            with st.expander("Estimated Impact"):
                                st.write(remediation.estimated_impact)
                        
                        # Notification Status
                        st.subheader("📢 Slack Notification")
                        if final_state.notification_status:
                            notif = final_state.notification_status
                            if notif.sent:
                                st.markdown(f'<div class="status-success">✅ Sent at {notif.timestamp}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="status-error">❌ {notif.error}</div>', unsafe_allow_html=True)
                    
                    # Cookbook Checklist (full width)
                    st.subheader("📚 DevOps Runbook Checklist")
                    if final_state.cookbook_checklist:
                        # Format as markdown
                        llm_client = LLMClient(openrouter_api_key, llm_model)
                        cookbook_agent = CookbookAgent(llm_client)
                        cookbook_md = cookbook_agent.format_as_markdown(final_state.cookbook_checklist)
                        
                        st.markdown(cookbook_md)
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Runbook",
                            data=cookbook_md,
                            file_name=f"runbook_{final_state.classified_incident.incident_type}.md",
                            mime="text/markdown"
                        )
                    
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                with st.expander("Show Full Traceback"):
                    st.code(traceback.format_exc())

with tab2:
    st.subheader("📖 About the System")
    
    st.markdown("""
    ## Multi-Agent DevOps Incident Analysis Suite
    
    This production-ready system uses a multi-agent architecture to automate incident analysis and response.
    
    ### 🤖 Agent Architecture
    
    **1. Log Classifier Agent**
    - Parses structured/semi-structured logs
    - Extracts: timestamp, service, severity, error code
    - Classifies incident type
    - Outputs structured JSON
    
    **2. Remediation Agent**
    - Uses RAG-style reasoning
    - Maps issues to root causes
    - Recommends specific fixes
    - Provides technical rationale
    
    **3. Cookbook Synthesizer Agent**
    - Converts plans to runbooks
    - Step-by-step checklists
    - Includes validation steps
    - Provides rollback plans
    
    **4. JIRA Ticket Agent**
    - Auto-creates tickets for CRITICAL incidents
    - Populates summary, description, priority
    - Attaches remediation plan
    
    **5. Notification Agent**
    - Sends formatted alerts to Slack
    - Includes severity and fix steps
    - Links to JIRA tickets
    
    **6. Orchestrator (LangGraph)**
    - Manages workflow state
    - Coordinates agent execution
    - Handles conditional logic
    
    ### 🔄 Workflow
    
    ```
    Log Input → Classify → Remediate → [JIRA if Critical] → Cookbook → Notify
    ```
    
    ### 🛠️ Technologies
    
    - **LangChain**: Agent framework
    - **LangGraph**: Workflow orchestration
    - **OpenRouter**: LLM access
    - **Streamlit**: Interactive UI
    - **Pydantic**: Structured outputs
    - **JIRA API**: Ticket management
    - **Slack**: Notifications
    
    ### 🚀 Features
    
    - Multi-agent collaboration
    - Traceable reasoning
    - Structured outputs
    - Production-ready code
    - Docker support
    - Modular design
    """)
    
    # Show graph visualization
    st.subheader("📊 Workflow Graph")
    if openrouter_api_key:
        state = IncidentAnalysisState(
            raw_log_input="",
            openrouter_api_key=openrouter_api_key,
            llm_model=llm_model
        )
        orchestrator = IncidentAnalysisOrchestrator(state)
        st.code(orchestrator.get_graph_visualization(), language="")
    else:
        st.info("Enter API key to view workflow graph")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Built with ❤️ using LangChain, LangGraph, and Streamlit<br>
        Multi-Agent AI for DevOps Excellence
    </div>
    """,
    unsafe_allow_html=True
)
