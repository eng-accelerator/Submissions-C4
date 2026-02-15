import requests
import os
import openai
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import plotly.graph_objects as go
from agent import run_agent

response = requests.get("http://localhost:8000/logs")
logs = response.json()

for log in logs:
    print(log)

# Streamlit UI
def main():
    st.title("🤖 AI Security Log Monitor")
    st.markdown("**Step-by-step autonomous processing** with real data and transparent decision making")
    
    # Initialize session state
    if 'processed_tickets' not in st.session_state:
        st.session_state.processed_tickets = []

      # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key - check .env first, fall back to text input
        load_dotenv()
        env_api_key = os.getenv("OPENROUTER_API_KEY")
        if env_api_key:
            api_key = env_api_key
            st.info("Using API key from .env file")
        else:
            api_key = st.text_input("OpenRouter API Key", type="password", help="Get your API key from https://openrouter.ai/keys")

        if api_key:
            try:
                # Test the API key with a simple call
                client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                    default_headers={
                        "HTTP-Referer": "https://github.com/yourusername/support-router",
                        "X-Title": "Support Ticket Router"
                    }
                )
                
                # Test API connection
                test_response = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test connection"}],
                    max_tokens=10
                )
                
                st.session_state.openrouter_client = client
                st.success("✅ Agentic System Ready")
                st.success(f"✅ API Test: {test_response.choices[0].message.content[:20]}...")
                
            except Exception as e:
                st.error(f"❌ API Key Error: {str(e)}")
                st.error("Please check your OpenRouter API key and ensure you have credits")
                st.info("💡 Make sure to:")
                st.write("1. Get API key from https://openrouter.ai/keys")
                st.write("2. Add credits to your OpenRouter account")
                st.write("3. Copy the key exactly as shown")
        
        st.divider()

        st.divider()
        
        # Statistics
        if st.session_state.processed_tickets:
            st.subheader("📊 Processing Stats")
            total_tickets = len(st.session_state.processed_tickets)
            st.metric("Tickets Processed", total_tickets)
            
            # Calculate success rate
            successful = sum(1 for t in st.session_state.processed_tickets 
                           if t.get('processing_complete', False))
            st.metric("Success Rate", f"{(successful/total_tickets)*100:.1f}%")


     # Main Interface
    st.markdown(
        """
        **Sentinel AI** goes beyond static rule sets and signature matching. Powered by advanced AI reasoning,
        our autonomous agent dynamically adapts its analysis strategy in real time — choosing the right combination
        of sequence, payload, and behavioral analyzers based on the threat landscape it discovers. The result?
        Faster, sharper, and more context-aware threat assessments that catch what traditional tools miss.
        """
    )
    st.header("Server Logs")
    st.subheader("Mock Data Logs to Demo Different Vulnerabilities:")

    if logs:
        vulnerability_types = [entry["vulnerability_type"] for entry in logs]
        selected_vuln = st.selectbox("Vulnerability Type", vulnerability_types)
        selected_logs = next(entry["logs"] for entry in logs if entry["vulnerability_type"] == selected_vuln)
        st.write(f"**{len(selected_logs)} Log Entries**")
        df = pd.DataFrame(selected_logs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No logs available.")

    st.header("What should we look for?")
    options = [
        "Show failed logins",
        "Detect SQL injection attempts",
        "Find credential stuffing patterns",
        "Custom..."
    ]

    selection = st.selectbox("User Query", options)

    if selection == "Custom...":
        query = st.text_input("Enter custom query")
    else:
        query = selection

    if not api_key:
        st.warning("No API key detected. Please enter your OpenRouter API key in the sidebar to get started.")
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

    if 'openrouter_client' not in st.session_state:
        st.warning("API key was entered but the connection has not been verified yet. Check the sidebar for status.")
        st.stop()

    if st.button("Run Agent", type="primary"):
        input_data = {
            "message": "Analyze this log",
            "selected_vuln": selected_vuln,
            "logs": selected_logs,
            "query": query
        }

        # passing the openrouter client is needed since the
        # user is entering it here in the UI
        with st.spinner("Running agent pipeline (LLM intent parsing + analysis + threat narrative)..."):
            result = run_agent(input_data, st.session_state.openrouter_client)


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
            path_cols[2].metric("Deep-Dive", deep_dive.get("attack_type", "None") if deep_dive else "Skipped")

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
            st.warning(f"Alert: **{alert_type}** (confidence: {alert_confidence:.0%})")

        risk_factors = result.get("risk_factors", [])
        if risk_factors:
            st.error("Risk Factors: " + ", ".join(risk_factors))

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
                        st.write(f"- **{label}:** {', '.join(str(v) for v in value)}")
                    elif isinstance(value, dict):
                        st.write(f"- **{label}:**")
                        st.json(value)
                    else:
                        st.write(f"- **{label}:** {value}")

        # AI-generated threat narrative
        threat_narrative = result.get("threat_narrative")
        if threat_narrative:
            st.subheader("AI Threat Analysis")
            st.info(threat_narrative)

        # Build a single DataFrame with all feature scores
        feature_data = {}
        for key, label in [
            ("sequence_features", "Sequence"),
            ("payload_features", "Payload"),
            ("behavior_features", "Behavior"),
        ]:
            features = result.get(key, {})
            for name, score in features.items():
                display_name = name.replace("_", " ").title()
                feature_data[display_name] = {"Score": score, "Category": label}

        if feature_data:
            chart_df = pd.DataFrame.from_dict(feature_data, orient="index")
            st.bar_chart(chart_df["Score"])

            # --- Radar Chart: max score per category ---
            st.subheader("Threat Profile (Radar)")
            categories = ["Sequence", "Payload", "Behavior"]
            cat_max_scores = [
                chart_df[chart_df["Category"] == cat]["Score"].max()
                for cat in categories
            ]
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
            st.plotly_chart(radar_fig, use_container_width=True)

            # --- Grouped Bar Chart by Category ---
            st.subheader("Feature Scores by Category")
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
            st.plotly_chart(heatmap_fig, use_container_width=True)

            # --- Pie / Donut Chart: weighted category contribution ---
            st.subheader("Risk Contribution by Category")
            weights = {"Sequence": 0.4, "Payload": 0.4, "Behavior": 0.2}
            weighted_scores = [
                cat_max_scores[i] * weights[cat] for i, cat in enumerate(categories)
            ]
            pie_fig = go.Figure(data=go.Pie(
                labels=categories,
                values=weighted_scores,
                hole=0.4,
                textinfo="label+percent",
            ))
            pie_fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(pie_fig, use_container_width=True)



main()
