import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0.3
)

def debt_analyzer(data):
    prompt = f"""
    Analyze the user's debt profile:
    {data}
    Provide:
    - Debt health
    - High interest risks
    - Payoff priority strategy
    - Snowball vs Avalanche suggestion
    """
    return llm.invoke(prompt).content


def savings_strategy(data):
    prompt = f"""
    Based on user financial data:
    {data}
    Create:
    - Monthly savings goal
    - Emergency fund plan
    - Short term & long term savings allocation
    """
    return llm.invoke(prompt).content


def investment_agent(data, risk_profile):
    prompt = f"""
    User Financial Data:
    {data}
    Risk Profile: {risk_profile}

    Suggest:
    - Asset allocation %
    - SIP strategy
    - Equity/Debt ratio
    - Expected annual return estimate
    - 10 year projection
    """
    return llm.invoke(prompt).content


def budget_advisor(data):
    prompt = f"""
    Analyze spending behavior:
    {data}

    Provide:
    - Budget correction suggestions
    - Spending cut areas
    - Optimization ideas
    """
    return llm.invoke(prompt).content
