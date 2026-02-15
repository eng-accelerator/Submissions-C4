"""
Configuration file for Multi-Agent Financial Advisor
Customize settings, thresholds, and agent behaviors here
"""

# API Configuration
API_CONFIG = {
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 4096,
    'temperature': 0.3,  # Lower = more consistent, Higher = more creative
}

# Financial Health Score Thresholds
HEALTH_SCORE_THRESHOLDS = {
    'excellent': 80,
    'good': 60,
    'fair': 40,
    'needs_improvement': 0,
}

# Savings Rate Recommendations
SAVINGS_RATE = {
    'excellent': 20,  # 20%+ of income
    'good': 15,       # 15-20% of income
    'adequate': 10,   # 10-15% of income
    'minimum': 5,     # 5-10% of income
}

# Debt-to-Income Ratio Guidelines
DEBT_TO_INCOME = {
    'excellent': 20,  # <20% is excellent
    'good': 36,       # <36% is good
    'concerning': 50, # <50% is concerning
    'critical': 75,   # >75% is critical
}

# Emergency Fund Recommendations
EMERGENCY_FUND = {
    'minimum_months': 3,
    'recommended_months': 6,
    'high_risk_months': 12,  # For self-employed or single income
}

# Budget Percentages (50/30/20 Rule)
BUDGET_PERCENTAGES = {
    'needs': 0.50,      # 50% for needs (housing, food, utilities)
    'wants': 0.30,      # 30% for wants (entertainment, dining)
    'savings_debt': 0.20,  # 20% for savings and debt repayment
}

# Investment Allocation by Age (Aggressive)
INVESTMENT_ALLOCATION_AGGRESSIVE = {
    '20s': {'stocks': 90, 'bonds': 10},
    '30s': {'stocks': 85, 'bonds': 15},
    '40s': {'stocks': 75, 'bonds': 25},
    '50s': {'stocks': 60, 'bonds': 40},
    '60s': {'stocks': 40, 'bonds': 60},
}

# Investment Allocation by Age (Moderate)
INVESTMENT_ALLOCATION_MODERATE = {
    '20s': {'stocks': 80, 'bonds': 20},
    '30s': {'stocks': 75, 'bonds': 25},
    '40s': {'stocks': 65, 'bonds': 35},
    '50s': {'stocks': 50, 'bonds': 50},
    '60s': {'stocks': 30, 'bonds': 70},
}

# Investment Allocation by Age (Conservative)
INVESTMENT_ALLOCATION_CONSERVATIVE = {
    '20s': {'stocks': 60, 'bonds': 40},
    '30s': {'stocks': 55, 'bonds': 45},
    '40s': {'stocks': 45, 'bonds': 55},
    '50s': {'stocks': 35, 'bonds': 65},
    '60s': {'stocks': 20, 'bonds': 80},
}

# Tax-Advantaged Account Contribution Limits (2024)
TAX_ADVANTAGED_LIMITS = {
    '401k': 23000,        # Annual limit
    '401k_catchup': 7500, # Additional for 50+
    'ira': 7000,          # Annual limit
    'ira_catchup': 1000,  # Additional for 50+
    'hsa_individual': 4150,
    'hsa_family': 8300,
    'hsa_catchup': 1000,  # Additional for 55+
}

# Debt Payoff Strategy Preferences
DEBT_STRATEGY = {
    'avalanche': {
        'name': 'Avalanche Method',
        'description': 'Pay highest interest rate first',
        'best_for': 'Minimizing total interest paid',
    },
    'snowball': {
        'name': 'Snowball Method',
        'description': 'Pay smallest balance first',
        'best_for': 'Quick psychological wins',
    },
}

# High Interest Rate Threshold
HIGH_INTEREST_THRESHOLD = 10.0  # Debts above this rate are considered high-interest

# Web Application Settings
WEB_APP_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,  # Set to False in production
    'max_upload_size_mb': 16,
    'allowed_extensions': ['txt', 'pdf', 'docx', 'csv', 'xlsx'],
    'upload_folder': 'uploads',
}

# Agent Analysis Preferences
AGENT_PREFERENCES = {
    'enable_web_search': False,  # Future feature
    'detailed_breakdown': True,
    'include_examples': True,
    'markdown_formatting': True,
}

# Display Formatting
CURRENCY_FORMAT = {
    'symbol': '$',
    'decimal_places': 2,
    'thousands_separator': ',',
}

# Financial Goals Templates
GOAL_TEMPLATES = {
    'emergency_fund': 'Build {months}-month emergency fund',
    'debt_payoff': 'Pay off {debt_name} by {date}',
    'house_down_payment': 'Save ${amount} for house down payment',
    'retirement': 'Reach ${amount} in retirement savings',
    'vacation': 'Save ${amount} for {destination} trip',
    'education': 'Save ${amount} for education fund',
}

# Risk Tolerance Profiles
RISK_PROFILES = {
    'conservative': {
        'description': 'Focus on capital preservation, lower returns',
        'volatility_tolerance': 'Low',
        'time_horizon': 'Short-term',
    },
    'moderate': {
        'description': 'Balanced approach, moderate returns',
        'volatility_tolerance': 'Medium',
        'time_horizon': 'Medium-term',
    },
    'aggressive': {
        'description': 'Maximize growth, accept higher risk',
        'volatility_tolerance': 'High',
        'time_horizon': 'Long-term',
    },
}

# Notification Thresholds
NOTIFICATION_THRESHOLDS = {
    'low_savings_rate': 5,        # Alert if savings rate below 5%
    'high_debt_ratio': 50,        # Alert if DTI above 50%
    'insufficient_emergency': 1,   # Alert if emergency fund < 1 month
    'high_interest_debt': 15,     # Alert if any debt above 15% APR
}

# Custom Agent Prompts (Advanced Users)
# Uncomment and modify to customize agent behavior
CUSTOM_PROMPTS = {
    # 'debt_analyzer': """
    #     Your custom debt analyzer prompt here...
    # """,
}

# Feature Flags
FEATURES = {
    'enable_document_upload': True,
    'enable_manual_input': True,
    'enable_comprehensive_analysis': True,
    'enable_export': True,
    'enable_goal_tracking': True,  # Future feature
    'enable_historical_comparison': False,  # Future feature
}

# Color Scheme for UI (CSS Variables)
COLOR_SCHEME = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#48bb78',
    'warning': '#f6ad55',
    'error': '#f56565',
    'info': '#4299e1',
}

# Export this configuration
def get_config(section=None):
    """
    Get configuration settings
    
    Args:
        section: Optional section name to get specific config
        
    Returns:
        dict: Configuration settings
    """
    config = {
        'api': API_CONFIG,
        'health_score': HEALTH_SCORE_THRESHOLDS,
        'savings_rate': SAVINGS_RATE,
        'debt_to_income': DEBT_TO_INCOME,
        'emergency_fund': EMERGENCY_FUND,
        'budget': BUDGET_PERCENTAGES,
        'investment_aggressive': INVESTMENT_ALLOCATION_AGGRESSIVE,
        'investment_moderate': INVESTMENT_ALLOCATION_MODERATE,
        'investment_conservative': INVESTMENT_ALLOCATION_CONSERVATIVE,
        'tax_limits': TAX_ADVANTAGED_LIMITS,
        'debt_strategy': DEBT_STRATEGY,
        'high_interest_threshold': HIGH_INTEREST_THRESHOLD,
        'web_app': WEB_APP_CONFIG,
        'agent_preferences': AGENT_PREFERENCES,
        'currency': CURRENCY_FORMAT,
        'goals': GOAL_TEMPLATES,
        'risk_profiles': RISK_PROFILES,
        'notifications': NOTIFICATION_THRESHOLDS,
        'features': FEATURES,
        'colors': COLOR_SCHEME,
    }
    
    if section:
        return config.get(section, {})
    return config


if __name__ == "__main__":
    # Print configuration summary
    import json
    print("Current Configuration:")
    print(json.dumps(get_config(), indent=2, default=str))
