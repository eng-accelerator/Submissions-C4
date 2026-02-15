import requests
import os
import openai
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import plotly.graph_objects as go
from agent import run_agent
import re
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
load_dotenv()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LOG_API_URL = os.getenv("LOG_API_URL", "http://localhost:8000/logs")
LOG_API_TOKEN = os.getenv("LOG_API_TOKEN", "")
MAX_LOGS_DISPLAY = 1000
QUERY_MAX_LENGTH = 200

# Allowed query patterns for input validation
ALLOWED_QUERY_PATTERNS = [
    r'^Show failed logins.*',
    r'^Detect .+ attempts.*',
    r'^Find .+ patterns.*',
    r'^Identify .+',
    r'^Analyze .+',
    r'^Search for .+',
]

@st.cache_data(ttl=60)
def fetch_logs() -> List[Dict[str, Any]]:
    """
    Fetch logs from API with error handling and authentication.
    Cached for 60 seconds to reduce API calls.
    """
    try:
        headers = {}
        if LOG_API_TOKEN:
            headers["Authorization"] = f"Bearer {LOG_API_TOKEN}"
        
        response = requests.get(
            LOG_API_URL,
            timeout=5,
            headers=headers
        )
        response.raise_for_status()
        logs = response.json()
        
        logger.info(f"Successfully fetched {len(logs)} log entries")
        return logs
        
    except requests.exceptions.Timeout:
        logger.error("Log API request timed out")
        st.error("⚠️ Log server is not responding. Please check if the server is running.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to log API")
        st.error("⚠️ Cannot connect to log server. Please ensure it's running at localhost:8000")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch logs: {e}")
        st.error(f"❌ Failed to fetch logs: {str(e)}")
        return []
    except ValueError as e:
        logger.error(f"Invalid JSON response: {e}")
        st.error("❌ Received invalid data from log server")
        return []

@st.cache_resource
def validate_api_key(api_key: str, base_url: str) -> Optional[openai.OpenAI]:
    """
    Validate API key and create client (cached to avoid repeated validation).
    Returns client if valid, None otherwise.
    """
    try:
        client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/support-router",
                "X-Title": "Support Ticket Router"
            }
        )
        
        # Test API connection with minimal token usage
        test_response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "OK"}],
            max_tokens=5
        )
        
        logger.info("API key validated successfully")
        return client
        
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return None

def sanitize_query(query: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.
    """
    if not query:
        return ""
    
    # Check against allowed patterns
    matches_pattern = any(re.match(pattern, query, re.IGNORECASE) 
                         for pattern in ALLOWED_QUERY_PATTERNS)
    
    if not matches_pattern:
        # Strip potentially dangerous characters
        query = re.sub(r'[^\w\s\-,.]', '', query)
    
    # Limit length
    query = query[:QUERY_MAX_LENGTH]
    
    # Remove common prompt injection attempts
    dangerous_phrases = [
        'ignore previous', 'ignore all', 'system:', 'assistant:',
        '<|im_start|>', '<|im_end|>', '###', '---END---'
    ]
    
    for phrase in dangerous_phrases:
        query = query.replace(phrase, '')
    
    return query.strip()

def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize dataframe to prevent XSS and limit cell content.
    """
    def sanitize_cell(x):
        if isinstance(x, str):
            # Limit string length
            x = x[:1000]
            # Remove HTML tags
            x = re.sub(r'<[^>]+>', '', x)
        return x
    
    return df.applymap(sanitize_cell)

def safe_render_text(text: str) -> str:
    """
    Sanitize text output from LLM to prevent XSS.
    """
    if not isinstance(text, str):
        return str(text)
    # Strip HTML tags
    return re.sub(r'<[^>]+>', '', text)

def validate_result_structure(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize result structure with safe defaults.
    """
    safe_result = {
        "analysis_mode": result.get("analysis_mode", "full"),
        "retry_count": max(0, min(int(result.get("retry_count", 0)), 10)),
        "deep_dive_findings": result.get("deep_dive_findings"),
        "risk_score": max(0.0, min(float(result.get("risk_score", 0)), 1.0)),
        "alert_type": result.get("alert_type"),
        "alert_confidence": max(0.0, min(float(result.get("alert_confidence", 0)), 1.0)),
        "risk_factors": result.get("risk_factors", []),
        "threat_narrative": safe_render_text(result.get("threat_narrative", "")),
        "sequence_features": result.get("sequence_features", {}),
        "payload_features": result.get("payload_features", {}),
        "behavior_features": result.get("behavior_features", {}),
    }
    return safe_result

def initialize_session_state():
    """
    Initialize all session state variables in one place.
    """
    if 'processed_tickets' not in st.session_state:
        st.session_state.processed_tickets = []
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = False
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""

@st.cache_data
def render_chart_radar(cat_max_scores: List[float], categories: List[str]):
    """Cached radar chart rendering"""
    radar_fig = go.Figure(data=go.Scatterpolar(
        r=cat_max_scores + [cat_max_scores[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="Risk Profile",
    ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return radar_fig

@st.cache_data
def render_chart_grouped(chart_df: pd.DataFrame, categories: List[str]):
    """Cached grouped bar chart rendering"""
    grouped_fig = go.Figure()
    for cat in categories:
        cat_data = chart_df[chart_df["Category"] == cat]
        grouped_fig.add_trace(go.Bar(
            x=cat_data.index,
            y=cat_data["Score"],
            name=cat,
        ))
    grouped_fig.update_layout(
        barmode="group",
        yaxis=dict(title="Score", range=[0, 1]),
        xaxis=dict(title="Feature"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return grouped_fig

@st.cache_data
def render_chart_heatmap(heatmap_z: List[List], all_features: List[str], categories: List[str]):
    """Cached heatmap rendering"""
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_z,
        x=all_features,
        y=categories,
        colorscale="RdYlGn_r",
        zmin=0, zmax=1,
        text=[[f"{v:.2f}" if v is not None else "" for v in row] for row in heatmap_z],
        texttemplate="%{text}",
        hovertemplate="Category: %{y}<br>Feature: %{x}<br>Score: %{z:.2f}<extra></extra>",
    ))
    heatmap_fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    return heatmap_fig

@st.cache_data
def render_chart_pie(weighted_scores: List[float], categories: List[str]):
    """Cached pie chart rendering"""
    pie_fig = go.Figure(data=go.Pie(
        labels=categories,
        values=weighted_scores,
        hole=0.4,
        textinfo="label+percent",
    ))
    pie_fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    return pie_fig

# Streamlit UI
def main():
    st.set_page_config(
        page_title="🤖 AI Security Log Monitor",
        page_icon="🛡️",
        layout="wide"
    )
    
    st.title("🤖 AI Security Log Monitor")
    st.markdown("**Step-by-step autonomous processing** with real data and transparent decision making")
    
    # Initialize session state
    initialize_session_state()
    
    # Fetch logs (cached)
    logs = fetch_logs()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key - check .env first, fall back to text input
        env_api_key = os.getenv("OPENROUTER_API_KEY")
        if env_api_key:
            api_key = env_api_key
            st.info("✅ Using API key from .env file")
        else:
            api_key = st.text_input(
                "OpenRouter API Key", 
                type="password", 
                help="Get your API key from https://openrouter.ai/keys"
            )

        # Validate API key (cached)
        client = None
        if api_key:
            client = validate_api_key(api_key, OPENROUTER_BASE_URL)
            
            if client:
                st.success("✅ Agentic System Ready")
                st.session_state.api_key_validated = True
            else:
                st.error("❌ API Key Error")
                st.error("Please check your OpenRouter API key and ensure you have credits")
                st.info("💡 Make sure to:")
                st.write("1. Get API key from https://openrouter.ai/keys")
                st.write("2. Add credits to your OpenRouter account")
                st.write("3. Copy the key exactly as shown")
                st.session_state.api_key_validated = False
        
        st.divider()
        
        # Statistics
        if st.session_state.processed_tickets:
            st.subheader("📊 Processing Stats")
            total_tickets = len(st.session_state.processed_tickets)
            st.metric("Tickets Processed", total_tickets)
            
            # Calculate success rate
            successful = sum(1 for t in st.session_state.processed_tickets 
                           if t.get('processing_complete', False))
            if total_tickets > 0:
                st.metric("Success Rate", f"{(successful/total_tickets)*100:.1f}%")

    # Main Interface
    st.header("Server Logs")
    st.subheader("Mock Data Logs to Demo Different Vulnerabilities:")

    selected_vuln = None
    selected_logs = []
    
    if logs:
        try:
            vulnerability_types = [entry.get("vulnerability_type", "Unknown") for entry in logs]
            selected_vuln = st.selectbox("Vulnerability Type", vulnerability_types)
            selected_logs = next(
                (entry.get("logs", []) for entry in logs 
                 if entry.get("vulnerability_type") == selected_vuln),
                []
            )
            
            if selected_logs:
                # Limit display for performance
                display_logs = selected_logs[:MAX_LOGS_DISPLAY]
                st.write(f"**{len(selected_logs)} Log Entries** (showing {len(display_logs)})")
                
                df = pd.DataFrame(display_logs)
                df = sanitize_dataframe(df)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No logs found for this vulnerability type.")
        except Exception as e:
            logger.error(f"Error processing logs: {e}")
            st.error("Error processing log data")
    else:
        st.info("No logs available. Please ensure the log server is running.")

    st.header("What should we look for?")
    options = [
        "Show failed logins",
        "Detect SQL injection attempts",
        "Find credential stuffing patterns",
        "Custom..."
    ]

    selection = st.selectbox("User Query", options)

    if selection == "Custom...":
        raw_query = st.text_input("Enter custom query")
        query = sanitize_query(raw_query)
        if raw_query != query:
            st.caption(f"Sanitized query: {query}")
    else:
        query = selection

    # API key check
    if not api_key:
        st.warning("⚠️ No API key detected. Please enter your OpenRouter API key in the sidebar to get started.")
        st.info(
            "**How to set up your API key:**\n"
            "1. Go to [openrouter.ai/keys](https://openrouter.ai/keys) and create an API key\n"
            "2. Enter it in the **OpenRouter API Key** field in the sidebar\n"
            "3. Alternatively, create a `.env` file in the project root with:\n"
            "   ```\n"
            "   OPENROUTER_API_KEY=your_key_here\n"
            "   ```"
        )
        st.stop()

    if not st.session_state.api_key_validated or not client:
        st.warning("⚠️ API key was entered but the connection has not been verified yet. Check the sidebar for status.")
        st.stop()

    if st.button("Run Agent", type="primary", disabled=(not selected_logs or not query)):
        if not selected_logs:
            st.error("No logs to analyze. Please select a vulnerability type with available logs.")
            st.stop()
            
        if not query:
            st.error("Please enter a query.")
            st.stop()
        
        # Log the analysis request
        logger.info(f"Running analysis - Query: {query[:100]} | Vuln Type: {selected_vuln}")
        
        input_data = {
            "message": "Analyze this log",
            "selected_vuln": selected_vuln,
            "logs": selected_logs,
            "query": query
        }

        # Run agent with error handling
        try:
            with st.spinner("Running agent pipeline (LLM intent parsing + analysis + threat narrative)..."):
                result = run_agent(input_data, client)
            
            # Validate result structure
            result = validate_result_structure(result)
            
            # Store in session state
            st.session_state.processed_tickets.append({
                'query': query,
                'vuln_type': selected_vuln,
                'processing_complete': True,
                'risk_score': result.get('risk_score', 0)
            })
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            st.error(f"❌ Analysis failed: {str(e)}")
            st.session_state.processed_tickets.append({
                'query': query,
                'vuln_type': selected_vuln,
                'processing_complete': False
            })
            st.stop()

        st.header('Security Vulnerabilities')

        # Agent decision path
        analysis_mode = result.get("analysis_mode", "full")
        retry_count = result.get("retry_count", 0)
        deep_dive = result.get("deep_dive_findings")

        mode_labels = {
            "full": "Full Analysis (all analyzers)",
            "payload_focus": "Payload-Focused (SQL/XSS/injection)",
            "sequence_focus": "Sequence-Focused (login/credential patterns)",
            "behavior_focus": "Behavior-Focused (anomalous users)",
        }

        with st.expander("Agent Decision Path", expanded=True):
            path_cols = st.columns(3)
            path_cols[0].metric("Analysis Mode", mode_labels.get(analysis_mode, analysis_mode))
            path_cols[1].metric("Retry Loops", retry_count)
            path_cols[2].metric(
                "Deep-Dive", 
                deep_dive.get("attack_type", "None") if deep_dive else "Skipped"
            )

            if retry_count > 0:
                st.caption("The agent widened from a focused scan to full analysis after initial results were inconclusive.")
            if deep_dive:
                st.caption(f"Specialist **{deep_dive.get('attack_type')}** analyzer ran for enriched findings.")

        st.subheader("Risk Assessment:")

        # Overall risk score
        risk_score = result.get("risk_score", 0)
        alert_type = result.get("alert_type")
        alert_confidence = result.get("alert_confidence", 0)

        if risk_score >= 0.7:
            risk_color = "🔴"
        elif risk_score >= 0.4:
            risk_color = "🟡"
        else:
            risk_color = "🟢"

        st.metric(
            label=f"{risk_color} Overall Risk Score",
            value=f"{risk_score:.0%}",
        )

        if alert_type:
            st.warning(f"Alert: **{safe_render_text(alert_type)}** (confidence: {alert_confidence:.0%})")

        risk_factors = result.get("risk_factors", [])
        if risk_factors:
            safe_factors = [safe_render_text(f) for f in risk_factors]
            st.error("Risk Factors: " + ", ".join(safe_factors))

        # Deep-dive specialist findings
        if deep_dive:
            st.subheader("Specialist Deep-Dive Findings")
            display_findings = {
                k: v for k, v in deep_dive.items()
                if k != "attack_type" and v and v != [] and v != {}
            }
            if display_findings:
                for key, value in display_findings.items():
                    label = key.replace("_", " ").title()
                    if isinstance(value, bool):
                        st.write(f"- **{label}:** {'Yes' if value else 'No'}")
                    elif isinstance(value, list):
                        safe_values = [safe_render_text(str(v)) for v in value[:10]]  # Limit list size
                        st.write(f"- **{label}:** {', '.join(safe_values)}")
                    elif isinstance(value, dict):
                        st.write(f"- **{label}:**")
                        st.json(value)
                    else:
                        st.write(f"- **{label}:** {safe_render_text(str(value))}")

        # AI-generated threat narrative
        threat_narrative = result.get("threat_narrative")
        if threat_narrative:
            st.subheader("AI Threat Analysis")
            st.info(threat_narrative)  # Already sanitized in validate_result_structure

        # Build a single DataFrame with all feature scores
        feature_data = {}
        for key, label in [
            ("sequence_features", "Sequence"),
            ("payload_features", "Payload"),
            ("behavior_features", "Behavior"),
        ]:
            features = result.get(key, {})
            for name, score in features.items():
                try:
                    score = max(0.0, min(float(score), 1.0))  # Clamp score
                    display_name = name.replace("_", " ").title()
                    feature_data[display_name] = {"Score": score, "Category": label}
                except (ValueError, TypeError):
                    logger.warning(f"Invalid score for feature {name}: {score}")
                    continue

        if feature_data:
            chart_df = pd.DataFrame.from_dict(feature_data, orient="index")
            st.bar_chart(chart_df["Score"])

            # --- Radar Chart: max score per category ---
            st.subheader("Threat Profile (Radar)")
            categories = ["Sequence", "Payload", "Behavior"]
            cat_max_scores = [
                chart_df[chart_df["Category"] == cat]["Score"].max() 
                if not chart_df[chart_df["Category"] == cat].empty else 0
                for cat in categories
            ]
            radar_fig = render_chart_radar(cat_max_scores, categories)
            st.plotly_chart(radar_fig, use_container_width=True)

            # --- Grouped Bar Chart by Category ---
            st.subheader("Feature Scores by Category")
            grouped_fig = render_chart_grouped(chart_df, categories)
            st.plotly_chart(grouped_fig, use_container_width=True)

            # --- Heatmap ---
            st.subheader("Feature Heatmap")
            all_features = chart_df.index.tolist()
            heatmap_z = []
            for cat in categories:
                row = []
                for feat in all_features:
                    if chart_df.loc[feat, "Category"] == cat:
                        row.append(chart_df.loc[feat, "Score"])
                    else:
                        row.append(None)
                heatmap_z.append(row)
            heatmap_fig = render_chart_heatmap(heatmap_z, all_features, categories)
            st.plotly_chart(heatmap_fig, use_container_width=True)

            # --- Pie / Donut Chart: weighted category contribution ---
            st.subheader("Risk Contribution by Category")
            weights = {"Sequence": 0.4, "Payload": 0.4, "Behavior": 0.2}
            weighted_scores = [
                cat_max_scores[i] * weights[cat] for i, cat in enumerate(categories)
            ]
            pie_fig = render_chart_pie(weighted_scores, categories)
            st.plotly_chart(pie_fig, use_container_width=True)

if __name__ == "__main__":
    main()
