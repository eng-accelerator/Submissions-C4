"""
Multi-Agent Financial Advisor Application
A comprehensive financial planning system with specialized AI agents
Supports both Anthropic and OpenRouter APIs
"""

import anthropic
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import re
from datetime import datetime, timedelta
import requests


class AgentType(Enum):
    """Types of financial advisor agents"""
    DOCUMENT_PARSER = "document_parser"
    DEBT_ANALYZER = "debt_analyzer"
    SAVINGS_STRATEGIST = "savings_strategist"
    BUDGET_OPTIMIZER = "budget_optimizer"
    INVESTMENT_ADVISOR = "investment_advisor"
    TAX_PLANNER = "tax_planner"
    EMERGENCY_FUND_BUILDER = "emergency_fund_builder"


@dataclass
class FinancialData:
    """Structured financial data extracted from documents"""
    monthly_income: float = 0.0
    expenses: Dict[str, float] = None
    debts: List[Dict[str, Any]] = None
    savings: float = 0.0
    investments: Dict[str, float] = None
    financial_goals: List[str] = None
    tax_bracket: Optional[float] = None
    
    def __post_init__(self):
        if self.expenses is None:
            self.expenses = {}
        if self.debts is None:
            self.debts = []
        if self.investments is None:
            self.investments = {}
        if self.financial_goals is None:
            self.financial_goals = []


class FinancialAdvisorAgent:
    """Base class for all financial advisor agents"""
    
    def __init__(self, agent_type: AgentType, api_key: Optional[str] = None, use_openrouter: bool = False):
        self.agent_type = agent_type
        self.use_openrouter = use_openrouter
        self.api_key = api_key
        
        if not use_openrouter:
            # Use Anthropic directly
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        else:
            # Use OpenRouter
            self.openrouter_api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
            if not self.openrouter_api_key:
                raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY environment variable.")
            self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            # Default to Claude on OpenRouter, but can be changed
            self.model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
            
        self.system_prompts = self._load_system_prompts()
    
    def _load_system_prompts(self) -> Dict[AgentType, str]:
        """Define specialized system prompts for each agent"""
        return {
            AgentType.DOCUMENT_PARSER: """You are a financial document parsing specialist. 
            Extract structured financial data from any document format including bank statements, 
            pay stubs, credit card statements, loan documents, investment statements, and budgets.
            
            Return data in this exact JSON structure:
            {
                "monthly_income": float,
                "expenses": {"category": amount},
                "debts": [{"name": str, "balance": float, "interest_rate": float, "minimum_payment": float, "type": str}],
                "savings": float,
                "investments": {"type": amount},
                "financial_goals": [str],
                "tax_bracket": float or null
            }""",
            
            AgentType.DEBT_ANALYZER: """You are a debt analysis and payoff specialist.
            Analyze debt portfolios and create optimized payoff strategies using avalanche method 
            (highest interest first) and snowball method (smallest balance first).
            
            Calculate:
            - Total debt burden
            - Weighted average interest rate
            - Debt-to-income ratio
            - Optimal payoff timeline
            - Monthly payment recommendations
            - Interest savings from early payoff
            - Debt consolidation opportunities""",
            
            AgentType.SAVINGS_STRATEGIST: """You are a personalized savings strategy expert.
            Create custom savings plans based on income, expenses, goals, and risk tolerance.
            
            Provide:
            - Emergency fund recommendations (3-6 months expenses)
            - Short-term savings goals (< 5 years)
            - Long-term savings strategies (> 5 years)
            - High-yield savings account recommendations
            - Automated savings schedules
            - Goal-based savings buckets""",
            
            AgentType.BUDGET_OPTIMIZER: """You are a budget optimization specialist.
            Analyze spending patterns and create actionable budget recommendations using 
            50/30/20 rule and zero-based budgeting principles.
            
            Provide:
            - Category-by-category spending analysis
            - Areas for cost reduction
            - Realistic budget targets
            - Discretionary spending optimization
            - Bill negotiation opportunities
            - Subscription audit recommendations""",
            
            AgentType.INVESTMENT_ADVISOR: """You are an investment strategy advisor.
            Recommend diversified investment strategies based on age, income, goals, and risk tolerance.
            
            Cover:
            - Asset allocation recommendations
            - Tax-advantaged accounts (401k, IRA, HSA)
            - Index fund vs active management
            - Dollar-cost averaging strategies
            - Rebalancing schedules
            - Retirement planning milestones""",
            
            AgentType.TAX_PLANNER: """You are a tax optimization strategist.
            Identify tax-saving opportunities and optimal timing for financial decisions.
            
            Analyze:
            - Tax-advantaged account maximization
            - Tax-loss harvesting opportunities
            - Deduction optimization
            - Retirement contribution strategies
            - Estimated tax payments
            - Year-end tax planning moves""",
            
            AgentType.EMERGENCY_FUND_BUILDER: """You are an emergency fund specialist.
            Design step-by-step plans to build adequate emergency reserves.
            
            Calculate:
            - Target emergency fund size (3-6 months expenses)
            - Monthly savings required
            - Timeline to full funding
            - Best account types for liquidity
            - Milestone rewards system
            - Cash flow management during building phase"""
        }
    
    def analyze(self, data: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute agent analysis with Claude API or OpenRouter"""
        system_prompt = self.system_prompts.get(self.agent_type, "You are a financial advisor.")
        
        if self.use_openrouter:
            return self._analyze_openrouter(data, system_prompt)
        else:
            return self._analyze_anthropic(data, system_prompt)
    
    def _analyze_anthropic(self, data: str, system_prompt: str) -> Dict[str, Any]:
        """Analyze using Anthropic API directly"""
        messages = [
            {
                "role": "user",
                "content": data
            }
        ]
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.3,
                system=system_prompt,
                messages=messages
            )
            
            result = response.content[0].text
            
            # Try to parse JSON responses from document parser
            if self.agent_type == AgentType.DOCUMENT_PARSER:
                try:
                    # Extract JSON from markdown code blocks if present
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
                    if json_match:
                        result = json_match.group(1)
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON", "raw_response": result}
            
            return {"response": result, "agent": self.agent_type.value}
            
        except Exception as e:
            return {"error": str(e), "agent": self.agent_type.value}
    
    def _analyze_openrouter(self, data: str, system_prompt: str) -> Dict[str, Any]:
        """Analyze using OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/verite-financial",  # Optional
                "X-Title": "Vérité Financial Advisor"  # Optional
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": data
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4096
            }
            
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            response.raise_for_status()
            result_data = response.json()
            
            # Extract the response text
            result = result_data['choices'][0]['message']['content']
            
            # Try to parse JSON responses from document parser
            if self.agent_type == AgentType.DOCUMENT_PARSER:
                try:
                    # Extract JSON from markdown code blocks if present
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
                    if json_match:
                        result = json_match.group(1)
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON", "raw_response": result}
            
            return {"response": result, "agent": self.agent_type.value}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"OpenRouter API error: {str(e)}", "agent": self.agent_type.value}
        except Exception as e:
            return {"error": str(e), "agent": self.agent_type.value}


class FinancialAdvisorOrchestrator:
    """Orchestrates multiple agents to provide comprehensive financial advice"""
    
    def __init__(self, api_key: Optional[str] = None, use_openrouter: bool = False):
        """
        Initialize orchestrator
        
        Args:
            api_key: API key for Anthropic or OpenRouter
            use_openrouter: If True, use OpenRouter API; if False, use Anthropic directly
        """
        self.use_openrouter = use_openrouter
        
        # Check environment variables if not provided
        if use_openrouter:
            api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable required when using OpenRouter")
        else:
            api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        self.agents = {
            agent_type: FinancialAdvisorAgent(agent_type, api_key, use_openrouter)
            for agent_type in AgentType
        }
        self.financial_data: Optional[FinancialData] = None
    
    def parse_documents(self, document_content: str) -> FinancialData:
        """Parse financial documents and extract structured data"""
        print("🔍 Document Parser Agent: Analyzing your financial documents...")
        
        parser_prompt = f"""
        Analyze this financial document and extract all relevant financial information.
        Document content:
        
        {document_content}
        
        Extract and structure the data according to the JSON schema. Be thorough and accurate.
        If information is missing, use 0 or empty lists/dicts as appropriate.
        """
        
        result = self.agents[AgentType.DOCUMENT_PARSER].analyze(parser_prompt)
        
        if "error" not in result:
            self.financial_data = FinancialData(**result)
            print("✅ Financial data extracted successfully!")
            return self.financial_data
        else:
            print(f"⚠️  Warning: {result.get('error', 'Unknown error')}")
            self.financial_data = FinancialData()
            return self.financial_data
    
    def analyze_debt(self) -> Dict[str, Any]:
        """Run debt analysis agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "debt_analyzer"
            }
        
        if not self.financial_data.debts or len(self.financial_data.debts) == 0:
            return {
                "response": """# No Debt Found

Good news! Based on the financial data provided, you don't currently have any outstanding debts recorded.

## Recommendations:

1. **Maintain Your Debt-Free Status**
   - Continue avoiding high-interest consumer debt
   - If you need to borrow, prioritize low-interest options
   - Build your credit through responsible credit card use (pay in full monthly)

2. **Build Emergency Fund**
   - Focus on saving 3-6 months of expenses
   - This prevents needing debt in emergencies

3. **Strategic Borrowing Only**
   - Mortgage for home purchase (typically good debt)
   - Low-interest education loans if needed
   - Avoid credit card debt and high-interest loans

Your debt-free status is a strong financial position. Keep it that way!""",
                "agent": "debt_analyzer"
            }
        
        print("\n💳 Debt Analyzer Agent: Creating optimized payoff plan...")
        
        debt_summary = f"""
        Analyze this debt portfolio and provide a comprehensive debt payoff strategy:
        
        Monthly Income: ${self.financial_data.monthly_income:,.2f}
        Current Savings: ${self.financial_data.savings:,.2f}
        
        Debts:
        """
        for i, debt in enumerate(self.financial_data.debts, 1):
            debt_summary += f"\n{i}. {debt.get('name', 'Unknown')}: ${debt.get('balance', 0):,.2f} @ {debt.get('interest_rate', 0)}% APR, Min Payment: ${debt.get('minimum_payment', 0):,.2f}"
        
        debt_summary += """
        
        Provide:
        1. Avalanche method payoff plan (highest interest first)
        2. Snowball method payoff plan (smallest balance first)
        3. Recommended extra payment amount based on income
        4. Total interest savings comparison
        5. Estimated debt-free date for each method
        6. Month-by-month payment allocation strategy
        """
        
        return self.agents[AgentType.DEBT_ANALYZER].analyze(debt_summary)
    
    def create_savings_strategy(self, goals: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run savings strategist agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "savings_strategist"
            }
        
        print("\n💰 Savings Strategist Agent: Designing personalized savings plan...")
        
        total_expenses = sum(self.financial_data.expenses.values())
        total_debt_payments = sum(debt.get('minimum_payment', 0) for debt in self.financial_data.debts)
        
        savings_prompt = f"""
        Create a personalized savings strategy based on this financial profile:
        
        Monthly Income: ${self.financial_data.monthly_income:,.2f}
        Monthly Expenses: ${total_expenses:,.2f}
        Monthly Debt Payments: ${total_debt_payments:,.2f}
        Current Savings: ${self.financial_data.savings:,.2f}
        
        Financial Goals: {', '.join(goals or self.financial_data.financial_goals or ['Build emergency fund', 'Save for retirement'])}
        
        Design a comprehensive savings strategy including:
        1. Emergency fund target and timeline
        2. Monthly savings recommendations by goal
        3. Automated savings schedule
        4. High-yield account recommendations
        5. Milestone celebration points
        6. Strategies to increase savings rate
        """
        
        return self.agents[AgentType.SAVINGS_STRATEGIST].analyze(savings_prompt)
    
    def optimize_budget(self) -> Dict[str, Any]:
        """Run budget optimizer agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "budget_optimizer"
            }
        
        print("\n📊 Budget Optimizer Agent: Analyzing spending and creating optimal budget...")
        
        budget_prompt = f"""
        Optimize this budget and identify cost-cutting opportunities:
        
        Monthly Income: ${self.financial_data.monthly_income:,.2f}
        Current Savings: ${self.financial_data.savings:,.2f}
        
        Monthly Expenses Breakdown:
        """
        
        if self.financial_data.expenses:
            for category, amount in self.financial_data.expenses.items():
                budget_prompt += f"\n- {category}: ${amount:,.2f}"
            
            total_expenses = sum(self.financial_data.expenses.values())
            budget_prompt += f"\n\nTotal Expenses: ${total_expenses:,.2f}"
            budget_prompt += f"\nNet Cash Flow: ${self.financial_data.monthly_income - total_expenses:,.2f}"
        else:
            budget_prompt += "\n(No expense breakdown provided - will provide general budgeting advice)"
        
        budget_prompt += """
        
        Provide:
        1. 50/30/20 budget analysis (needs/wants/savings)
        2. Specific cost-cutting recommendations by category
        3. Realistic target budget by category
        4. Subscription audit suggestions
        5. Bill negotiation opportunities
        6. Expected monthly savings from optimizations
        """
        
        return self.agents[AgentType.BUDGET_OPTIMIZER].analyze(budget_prompt)
    
    def investment_advice(self, risk_tolerance: str = "moderate") -> Dict[str, Any]:
        """Run investment advisor agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "investment_advisor"
            }
        
        print("\n📈 Investment Advisor Agent: Developing investment strategy...")
        
        investment_prompt = f"""
        Provide investment recommendations for this financial profile:
        
        Monthly Income: ${self.financial_data.monthly_income:,.2f}
        Current Savings: ${self.financial_data.savings:,.2f}
        Current Investments: {json.dumps(self.financial_data.investments, indent=2) if self.financial_data.investments else "None"}
        Risk Tolerance: {risk_tolerance}
        Age/Stage: Working professional (assume 30-40 years old if not specified)
        
        Provide:
        1. Recommended asset allocation
        2. Tax-advantaged account prioritization (401k, IRA, HSA)
        3. Specific investment vehicle recommendations
        4. Dollar-cost averaging strategy
        5. Rebalancing schedule
        6. Expected long-term returns
        """
        
        return self.agents[AgentType.INVESTMENT_ADVISOR].analyze(investment_prompt)
    
    def tax_optimization(self) -> Dict[str, Any]:
        """Run tax planner agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "tax_planner"
            }
        
        print("\n🏛️ Tax Planner Agent: Identifying tax optimization opportunities...")
        
        tax_prompt = f"""
        Identify tax optimization strategies for this financial profile:
        
        Annual Income: ${self.financial_data.monthly_income * 12:,.2f}
        Tax Bracket: {self.financial_data.tax_bracket or 'Unknown (please estimate based on income)'}
        Current Investments: {json.dumps(self.financial_data.investments, indent=2) if self.financial_data.investments else "None"}
        
        Provide:
        1. Tax-advantaged account contribution recommendations
        2. Tax-loss harvesting opportunities
        3. Deduction optimization strategies
        4. Estimated tax savings from recommendations
        5. Year-end tax planning checklist
        6. Retirement contribution strategy for tax benefits
        """
        
        return self.agents[AgentType.TAX_PLANNER].analyze(tax_prompt)
    
    def emergency_fund_plan(self) -> Dict[str, Any]:
        """Run emergency fund builder agent"""
        if not self.financial_data:
            return {
                "response": "No financial data available. Please upload financial documents or enter your data manually first.",
                "agent": "emergency_fund_builder"
            }
        
        print("\n🚨 Emergency Fund Builder Agent: Creating emergency fund plan...")
        
        total_expenses = sum(self.financial_data.expenses.values())
        total_debt_payments = sum(debt.get('minimum_payment', 0) for debt in self.financial_data.debts)
        
        emergency_prompt = f"""
        Design an emergency fund building plan:
        
        Monthly Income: ${self.financial_data.monthly_income:,.2f}
        Monthly Expenses: ${total_expenses:,.2f}
        Monthly Debt Payments: ${total_debt_payments:,.2f}
        Current Savings: ${self.financial_data.savings:,.2f}
        
        Essential Monthly Costs: ${total_expenses + total_debt_payments:,.2f}
        
        Provide:
        1. Target emergency fund amount (3-6 months of expenses)
        2. Current gap to target
        3. Recommended monthly savings amount
        4. Timeline to full funding
        5. Best account types for emergency funds
        6. Milestone celebration strategy (25%, 50%, 75%, 100%)
        7. How to balance emergency fund vs. debt payoff
        """
        
        return self.agents[AgentType.EMERGENCY_FUND_BUILDER].analyze(emergency_prompt)
    
    def comprehensive_financial_plan(self) -> Dict[str, Any]:
        """Generate a complete financial plan using all agents"""
        if not self.financial_data:
            return {"message": "No financial data available. Upload financial documents first."}
        
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE FINANCIAL ANALYSIS")
        print("="*60)
        
        results = {
            "summary": self._generate_summary(),
            "debt_analysis": self.analyze_debt(),
            "savings_strategy": self.create_savings_strategy(),
            "budget_optimization": self.optimize_budget(),
            "investment_advice": self.investment_advice(),
            "tax_optimization": self.tax_optimization(),
            "emergency_fund": self.emergency_fund_plan(),
            "timestamp": datetime.now().isoformat()
        }
        
        return results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate financial health summary"""
        total_expenses = sum(self.financial_data.expenses.values())
        total_debt = sum(debt.get('balance', 0) for debt in self.financial_data.debts)
        total_debt_payments = sum(debt.get('minimum_payment', 0) for debt in self.financial_data.debts)
        
        net_income = self.financial_data.monthly_income - total_expenses - total_debt_payments
        savings_rate = (net_income / self.financial_data.monthly_income * 100) if self.financial_data.monthly_income > 0 else 0
        debt_to_income = (total_debt / (self.financial_data.monthly_income * 12) * 100) if self.financial_data.monthly_income > 0 else 0
        
        return {
            "monthly_income": self.financial_data.monthly_income,
            "monthly_expenses": total_expenses,
            "monthly_debt_payments": total_debt_payments,
            "net_monthly_cash_flow": net_income,
            "total_debt": total_debt,
            "current_savings": self.financial_data.savings,
            "savings_rate_percent": round(savings_rate, 2),
            "debt_to_income_ratio_percent": round(debt_to_income, 2),
            "financial_health_score": self._calculate_health_score(savings_rate, debt_to_income)
        }
    
    def _calculate_health_score(self, savings_rate: float, debt_to_income: float) -> str:
        """Calculate overall financial health score"""
        score = 0
        
        # Savings rate scoring (0-40 points)
        if savings_rate >= 20:
            score += 40
        elif savings_rate >= 15:
            score += 30
        elif savings_rate >= 10:
            score += 20
        elif savings_rate >= 5:
            score += 10
        
        # Debt-to-income scoring (0-40 points)
        if debt_to_income <= 20:
            score += 40
        elif debt_to_income <= 36:
            score += 30
        elif debt_to_income <= 50:
            score += 20
        elif debt_to_income <= 75:
            score += 10
        
        # Emergency fund scoring (0-20 points)
        if self.financial_data.savings > 0:
            monthly_expenses = sum(self.financial_data.expenses.values())
            if monthly_expenses > 0:
                months_covered = self.financial_data.savings / monthly_expenses
                if months_covered >= 6:
                    score += 20
                elif months_covered >= 3:
                    score += 15
                elif months_covered >= 1:
                    score += 10
                else:
                    score += 5
        
        if score >= 80:
            return f"Excellent ({score}/100)"
        elif score >= 60:
            return f"Good ({score}/100)"
        elif score >= 40:
            return f"Fair ({score}/100)"
        else:
            return f"Needs Improvement ({score}/100)"


def main():
    """Main function to demonstrate the financial advisor system"""
    print("="*60)
    print("🏦 MULTI-AGENT FINANCIAL ADVISOR SYSTEM")
    print("="*60)
    
    # Check which API to use
    use_openrouter = os.environ.get('USE_OPENROUTER', 'false').lower() == 'true'
    
    if use_openrouter:
        print("\n🌐 Using OpenRouter API")
        model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        print(f"Model: {model}")
    else:
        print("\n🤖 Using Anthropic API directly")
        print("Model: claude-sonnet-4-20250514")
    
    print("\nInitializing agents...")
    
    # Initialize orchestrator
    orchestrator = FinancialAdvisorOrchestrator(use_openrouter=use_openrouter)
    
    # Sample financial document (in real app, this would come from user upload)
    sample_document = """
    FINANCIAL SUMMARY - December 2024
    
    INCOME:
    - Salary (after tax): $5,800/month
    - Freelance work: $800/month
    Total Monthly Income: $6,600
    
    MONTHLY EXPENSES:
    - Rent: $1,800
    - Utilities: $150
    - Groceries: $600
    - Transportation: $300
    - Insurance: $200
    - Entertainment: $250
    - Dining Out: $400
    - Subscriptions: $85
    - Phone: $70
    - Internet: $60
    
    DEBTS:
    1. Credit Card A: $8,500 balance, 18.99% APR, $170 minimum payment
    2. Credit Card B: $3,200 balance, 22.50% APR, $80 minimum payment
    3. Student Loan: $28,000 balance, 4.5% APR, $310 minimum payment
    4. Car Loan: $12,000 balance, 6.2% APR, $280 minimum payment
    
    SAVINGS:
    - Emergency Fund: $2,500
    - General Savings: $1,200
    Total Savings: $3,700
    
    INVESTMENTS:
    - 401(k): $18,500
    - IRA: $8,200
    
    FINANCIAL GOALS:
    - Pay off high-interest credit cards
    - Build 6-month emergency fund
    - Save for house down payment
    - Increase retirement savings
    """
    
    # Parse documents
    print("\n" + "-"*60)
    financial_data = orchestrator.parse_documents(sample_document)
    
    # Display extracted data
    print("\n📋 EXTRACTED FINANCIAL DATA:")
    print(f"Monthly Income: ${financial_data.monthly_income:,.2f}")
    print(f"Total Expenses: ${sum(financial_data.expenses.values()):,.2f}")
    print(f"Number of Debts: {len(financial_data.debts)}")
    print(f"Total Savings: ${financial_data.savings:,.2f}")
    
    # Run comprehensive analysis
    print("\n" + "-"*60)
    print("Running multi-agent analysis...\n")
    
    comprehensive_plan = orchestrator.comprehensive_financial_plan()
    
    # Display results
    print("\n" + "="*60)
    print("📊 FINANCIAL HEALTH SUMMARY")
    print("="*60)
    summary = comprehensive_plan['summary']
    for key, value in summary.items():
        formatted_key = key.replace('_', ' ').title()
        if isinstance(value, (int, float)) and 'percent' not in key.lower():
            print(f"{formatted_key}: ${value:,.2f}")
        else:
            print(f"{formatted_key}: {value}")
    
    print("\n" + "="*60)
    print("✅ COMPREHENSIVE FINANCIAL PLAN GENERATED")
    print("="*60)
    print("\nAll agent analyses completed successfully!")
    print("Review each section above for detailed recommendations.")
    print("\n💡 TIP: This system can be integrated with a web UI")
    print("    or used via API for real-time financial advice.")


if __name__ == "__main__":
    main()
