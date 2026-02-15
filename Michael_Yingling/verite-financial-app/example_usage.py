"""
Example Usage Script for Multi-Agent Financial Advisor
Demonstrates how to use the system programmatically
"""

from financial_advisor_app import FinancialAdvisorOrchestrator, FinancialData
import json


def example_1_from_document():
    """Example 1: Parse financial data from a document string"""
    print("=" * 60)
    print("EXAMPLE 1: Parsing Financial Document")
    print("=" * 60)
    
    # Sample document (could be from file upload)
    document = """
    Monthly Income: $7,500 (after tax)
    
    Monthly Expenses:
    - Rent: $2,000
    - Groceries: $500
    - Car Payment: $400
    - Insurance: $250
    - Utilities: $200
    - Entertainment: $300
    
    Debts:
    - Credit Card: $5,000 at 19.99% APR, $150 minimum
    - Student Loan: $35,000 at 5.5% APR, $380 minimum
    
    Current Savings: $8,000
    """
    
    orchestrator = FinancialAdvisorOrchestrator()
    financial_data = orchestrator.parse_documents(document)
    
    print(f"\nExtracted Data:")
    print(f"Income: ${financial_data.monthly_income:,.2f}")
    print(f"Savings: ${financial_data.savings:,.2f}")
    print(f"Debts: {len(financial_data.debts)}")
    
    return orchestrator


def example_2_manual_data():
    """Example 2: Create financial data manually"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Manual Financial Data")
    print("=" * 60)
    
    # Create data manually
    financial_data = FinancialData(
        monthly_income=6000.0,
        expenses={
            "Rent": 1500.0,
            "Groceries": 600.0,
            "Transportation": 300.0,
            "Utilities": 150.0,
            "Entertainment": 200.0,
            "Phone": 80.0
        },
        debts=[
            {
                "name": "Credit Card A",
                "balance": 8000.0,
                "interest_rate": 21.99,
                "minimum_payment": 200.0,
                "type": "credit_card"
            },
            {
                "name": "Car Loan",
                "balance": 15000.0,
                "interest_rate": 5.5,
                "minimum_payment": 350.0,
                "type": "auto_loan"
            }
        ],
        savings=5000.0,
        investments={
            "401k": 25000.0,
            "IRA": 10000.0
        },
        financial_goals=[
            "Pay off credit cards",
            "Build 6-month emergency fund",
            "Save for vacation"
        ]
    )
    
    orchestrator = FinancialAdvisorOrchestrator()
    orchestrator.financial_data = financial_data
    
    print("\nManual Data Created Successfully!")
    print(f"Income: ${financial_data.monthly_income:,.2f}")
    print(f"Total Expenses: ${sum(financial_data.expenses.values()):,.2f}")
    
    return orchestrator


def example_3_specific_agent():
    """Example 3: Run specific agent analysis"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Specific Agent Analysis")
    print("=" * 60)
    
    orchestrator = example_2_manual_data()
    
    # Run debt analysis only
    print("\n🔍 Running Debt Analyzer Agent...")
    debt_analysis = orchestrator.analyze_debt()
    
    if 'response' in debt_analysis:
        print("\n" + "-" * 60)
        print("DEBT ANALYSIS RESULTS:")
        print("-" * 60)
        print(debt_analysis['response'])
    
    return orchestrator


def example_4_comprehensive_plan():
    """Example 4: Generate comprehensive financial plan"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Comprehensive Financial Plan")
    print("=" * 60)
    
    orchestrator = example_2_manual_data()
    
    # Run all agents
    print("\n🚀 Running comprehensive analysis (all agents)...")
    comprehensive_plan = orchestrator.comprehensive_financial_plan()
    
    # Display summary
    print("\n" + "=" * 60)
    print("FINANCIAL HEALTH SUMMARY")
    print("=" * 60)
    
    summary = comprehensive_plan['summary']
    print(f"Monthly Income: ${summary['monthly_income']:,.2f}")
    print(f"Monthly Expenses: ${summary['monthly_expenses']:,.2f}")
    print(f"Net Cash Flow: ${summary['net_monthly_cash_flow']:,.2f}")
    print(f"Savings Rate: {summary['savings_rate_percent']:.1f}%")
    print(f"Debt-to-Income: {summary['debt_to_income_ratio_percent']:.1f}%")
    print(f"Financial Health: {summary['financial_health_score']}")
    
    # Save results to JSON
    with open('/home/claude/comprehensive_plan.json', 'w') as f:
        # Convert to serializable format
        serializable_plan = {
            'timestamp': comprehensive_plan['timestamp'],
            'summary': comprehensive_plan['summary'],
            'debt_analysis': {'status': 'completed' if 'response' in comprehensive_plan['debt_analysis'] else 'skipped'},
            'savings_strategy': {'status': 'completed' if 'response' in comprehensive_plan['savings_strategy'] else 'skipped'},
            'budget_optimization': {'status': 'completed' if 'response' in comprehensive_plan['budget_optimization'] else 'skipped'},
            'investment_advice': {'status': 'completed' if 'response' in comprehensive_plan['investment_advice'] else 'skipped'},
            'tax_optimization': {'status': 'completed' if 'response' in comprehensive_plan['tax_optimization'] else 'skipped'},
            'emergency_fund': {'status': 'completed' if 'response' in comprehensive_plan['emergency_fund'] else 'skipped'}
        }
        json.dump(serializable_plan, f, indent=2)
    
    print("\n✅ Results saved to: comprehensive_plan.json")
    
    return orchestrator


def example_5_custom_goals():
    """Example 5: Savings strategy with custom goals"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Custom Savings Goals")
    print("=" * 60)
    
    orchestrator = example_2_manual_data()
    
    custom_goals = [
        "Save $30,000 for house down payment in 3 years",
        "Build $20,000 emergency fund in 12 months",
        "Save $5,000 for vacation in 6 months"
    ]
    
    print("\n🎯 Custom Goals:")
    for goal in custom_goals:
        print(f"  • {goal}")
    
    print("\n💰 Running Savings Strategist Agent...")
    savings_strategy = orchestrator.create_savings_strategy(custom_goals)
    
    if 'response' in savings_strategy:
        print("\n" + "-" * 60)
        print("SAVINGS STRATEGY:")
        print("-" * 60)
        print(savings_strategy['response'])
    
    return orchestrator


def example_6_investment_risk_profile():
    """Example 6: Investment advice with risk tolerance"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Investment Advice by Risk Profile")
    print("=" * 60)
    
    orchestrator = example_2_manual_data()
    
    risk_profiles = ["conservative", "moderate", "aggressive"]
    
    for risk_level in risk_profiles:
        print(f"\n📈 Investment Advice - {risk_level.upper()} Risk Profile")
        print("-" * 60)
        
        investment_advice = orchestrator.investment_advice(risk_tolerance=risk_level)
        
        if 'response' in investment_advice:
            # Print first 500 characters as preview
            response = investment_advice['response']
            preview = response[:500] + "..." if len(response) > 500 else response
            print(preview)
            print()


def example_7_export_summary():
    """Example 7: Export financial summary to JSON"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Export Financial Summary")
    print("=" * 60)
    
    orchestrator = example_2_manual_data()
    summary = orchestrator._generate_summary()
    
    # Export to JSON
    export_file = '/home/claude/financial_summary.json'
    with open(export_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Financial summary exported to: {export_file}")
    print("\nSummary Contents:")
    print(json.dumps(summary, indent=2))
    
    return summary


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("  MULTI-AGENT FINANCIAL ADVISOR - USAGE EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates various ways to use the financial advisor system")
    print("\nNote: Set ANTHROPIC_API_KEY environment variable before running")
    print("\n" + "=" * 70)
    
    try:
        # Run examples
        example_1_from_document()
        
        example_2_manual_data()
        
        example_3_specific_agent()
        
        # Uncomment to run comprehensive analysis (takes longer)
        # example_4_comprehensive_plan()
        
        example_5_custom_goals()
        
        # Uncomment to see investment advice for different risk profiles
        # example_6_investment_risk_profile()
        
        example_7_export_summary()
        
        print("\n" + "=" * 70)
        print("  ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\n💡 Next Steps:")
        print("  1. Review the output above")
        print("  2. Check exported JSON files")
        print("  3. Try modifying the example data")
        print("  4. Run the web app: python web_app.py")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  • Ensure ANTHROPIC_API_KEY is set")
        print("  • Check your internet connection")
        print("  • Verify all dependencies are installed")


if __name__ == "__main__":
    main()
