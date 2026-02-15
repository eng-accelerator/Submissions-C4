import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from agents import debt_analyzer, savings_strategy, investment_agent, budget_advisor
from financial_engine import calculate_financial_health
from scenario_engine import forecast_cash_flow, simulate_scenario
from utils import generate_alerts, parse_bank_statement_pdf

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Financial Coach Pro",
    page_icon="💎",
    layout="wide"
)

# =====================================================
# SESSION STATE INIT
# =====================================================
if "expenses_data" not in st.session_state:
    st.session_state.expenses_data = pd.DataFrame(
        columns=["Date", "Category", "Amount", "Description"]
    )

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# =====================================================
# SIDEBAR (ONLY SETTINGS)
# =====================================================
st.sidebar.header("⚙️ Settings")
theme_toggle = st.sidebar.toggle("🌙 Dark Mode", value=True)
st.session_state.theme = "Dark" if theme_toggle else "Light"

# =====================================================
# THEME VARIABLES
# =====================================================
if st.session_state.theme == "Dark":
    bg_color = "#0B0F19"
    card_bg = "rgba(255,255,255,0.05)"
    text_color = "#FFFFFF"
    accent = "#00F5A0"
    chart_template = "plotly_dark"
else:
    bg_color = "#F4F7FA"
    card_bg = "rgba(255,255,255,0.7)"
    text_color = "#0E1117"
    accent = "#2563EB"
    chart_template = "plotly_white"

# =====================================================
# PREMIUM CSS
# =====================================================
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.main {{
    background: {bg_color};
}}

.navbar {{
    background: linear-gradient(90deg, #1E3A8A, #2563EB);
    padding: 18px;
    border-radius: 15px;
    color: white;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 25px;
}}

.glass-card {{
    background: {card_bg};
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    transition: 0.3s ease;
    margin-bottom: 20px;
}}

.glass-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}}

.kpi-title {{
    font-size: 14px;
    opacity: 0.7;
}}

.kpi-value {{
    font-size: 28px;
    font-weight: 600;
    color: {accent};
}}

.section-title {{
    font-size: 20px;
    margin-bottom: 15px;
    color: {text_color};
}}

div.stButton > button {{
    border-radius: 10px;
    height: 45px;
    font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# TOP NAVBAR
# =====================================================
st.markdown("""
<div class="navbar">
💎 AI Financial Coach Pro
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns([1, 1, 6])

with nav1:
    if st.button("🏠 Dashboard"):
        st.session_state.page = "Dashboard"

with nav2:
    if st.button("💸 Expense Tracker"):
        st.session_state.page = "Expense"

st.markdown("<hr>", unsafe_allow_html=True)

menu = st.session_state.page

# =====================================================
# DASHBOARD
# =====================================================
if menu == "Dashboard":

    # DASHBOARD HEADER
    st.markdown('<div class="section-title">📊 Financial Dashboard</div>', unsafe_allow_html=True)

    # INITIALIZE DEFAULT VALUES
    income = 0
    savings = 0
    debt = 0
    liquid_cash = 0
    risk_profile = "Moderate"
    scenario = "None"
    
    # FINANCIAL DATA & SETTINGS EXPANDER
    with st.expander("📝 Financial Data & Settings", expanded=True):
        uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type="pdf")
        
        if uploaded_file:
            if "parsed_data" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
                with st.spinner("Parsing Bank Statement..."):
                    parsed_df = parse_bank_statement_pdf(uploaded_file)
                    st.session_state.parsed_data = parsed_df
                    st.session_state.last_uploaded = uploaded_file.name
                    st.success(f"Extracted {len(parsed_df)} transactions")
        
        if "parsed_data" in st.session_state and not st.session_state.parsed_data.empty:
            if st.button("📥 Use Extracted Data"):
                # Filter Expenses
                expenses_df = st.session_state.parsed_data[st.session_state.parsed_data['Type'] == 'Expense']
                st.session_state.expenses_data = expenses_df
                
                # Calculate Income from 'Income' type transactions
                income_df = st.session_state.parsed_data[st.session_state.parsed_data['Type'] == 'Income']
                if not income_df.empty:
                    calculated_income = income_df['Amount'].sum()
                    st.session_state.calculated_income = calculated_income
                    st.success(f"Expenses updated! Income detected: ₹ {calculated_income:,.0f}")
                else:
                    st.success("Expenses updated from statement!")
                
                st.rerun()

    # Determine Income to use (Calculated from PDF)
    income = st.session_state.get("calculated_income", 0)

    total_expenses = (
        st.session_state.expenses_data["Amount"].sum()
        if not st.session_state.expenses_data.empty
        else 0
    )

    if income == 0 and total_expenses == 0:
        st.info("👋 Welcome! Please upload your Bank Statement PDF in the 'Financial Data & Settings' section to proceed.")
    
    elif st.button("🚀 Run Full Analysis"):

        score = calculate_financial_health(
            income, total_expenses, savings, debt, liquid_cash
        )

        net_balance = income - total_expenses
        savings_rate = (savings / income * 100) if income > 0 else 0

        # KPI CARDS
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-title">Net Balance</div>
                <div class="kpi-value">₹ {net_balance:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-title">Savings Rate</div>
                <div class="kpi-value">{savings_rate:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-title">Total Expenses</div>
                <div class="kpi-value">₹ {total_expenses:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-title">Health Score</div>
                <div class="kpi-value">{score}/100</div>
            </div>
            """, unsafe_allow_html=True)

        # GAUGE
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': "Financial Health"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': accent},
                'steps': [
                    {'range': [0, 40], 'color': "#EF4444"},
                    {'range': [40, 70], 'color': "#F59E0B"},
                    {'range': [70, 100], 'color': "#10B981"},
                ],
            }
        ))
        gauge.update_layout(template=chart_template, height=350)
        st.plotly_chart(gauge, use_container_width=True)

        # EXPENSE PIE
        if not st.session_state.expenses_data.empty:
            summary = st.session_state.expenses_data.groupby("Category")["Amount"].sum().reset_index()
            fig = px.pie(summary, values="Amount", names="Category",
                         hole=0.5, title="Expense Breakdown")
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

        # FORECAST
        forecast = forecast_cash_flow(income, total_expenses)
        years = [f"Year {i+1}" for i in range(len(forecast))]
        fig2 = px.line(x=years, y=forecast,
                       markers=True,
                       title="5-Year Cash Flow Forecast")
        fig2.update_layout(template=chart_template)
        st.plotly_chart(fig2, use_container_width=True)

        # AI INSIGHTS
        data = {
            "Income": income,
            "Expenses": total_expenses,
            "Savings": savings,
            "Debt": debt,
            "Liquid Cash": liquid_cash
        }

        st.markdown('<div class="section-title">🤖 AI Insights</div>', unsafe_allow_html=True)

        for output in [
            debt_analyzer(data),
            savings_strategy(data),
            investment_agent(data, risk_profile),
            budget_advisor(data)
        ]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write(output)
            st.markdown('</div>', unsafe_allow_html=True)

        if scenario != "None":
            result = simulate_scenario(income, total_expenses, scenario)
            st.info(f"Projected Monthly Balance under '{scenario}': ₹ {result:,.0f}")

        alerts = generate_alerts(income, total_expenses, False)
        for alert in alerts:
            st.warning(alert)

# =====================================================
# EXPENSE TRACKER
# =====================================================
elif menu == "Expense":

    st.markdown('<div class="section-title">💸 Expense Tracker</div>', unsafe_allow_html=True)

    with st.form("expense_form"):
        date = st.date_input("Date", datetime.today())
        category = st.selectbox("Category", [
            "Food", "Transport", "Rent", "Shopping",
            "Bills", "Entertainment", "Health", "Other"
        ])
        amount = st.number_input("Amount", 0, 1000000, 0)
        description = st.text_input("Description")
        submitted = st.form_submit_button("Add Expense")

        if submitted and amount > 0:
            new_expense = pd.DataFrame([{
                "Date": date,
                "Category": category,
                "Amount": amount,
                "Description": description
            }])
            st.session_state.expenses_data = pd.concat(
                [st.session_state.expenses_data, new_expense],
                ignore_index=True
            )
            st.success("Expense Added Successfully!")

    if not st.session_state.expenses_data.empty:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.dataframe(st.session_state.expenses_data, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        summary = st.session_state.expenses_data.groupby("Category")["Amount"].sum().reset_index()
        fig = px.bar(summary, x="Category", y="Amount",
                     title="Expenses by Category")
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

        total = st.session_state.expenses_data["Amount"].sum()
        st.metric("Total Monthly Expense", f"₹ {total:,.0f}")
