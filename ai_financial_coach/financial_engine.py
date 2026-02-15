def calculate_financial_health(income, expenses, savings, debt, liquid_cash):

    # Prevent division by zero
    savings_rate = (savings / income) if income > 0 else 0
    debt_ratio = (debt / income) if income > 0 else 0
    liquidity_ratio = (liquid_cash / expenses) if expenses > 0 else liquid_cash

    score = 100

    # Savings health
    if savings_rate < 0.2:
        score -= 20

    # Debt health
    if debt_ratio > 0.4:
        score -= 25

    # Liquidity health (at least 3 months expenses)
    if expenses > 0:
        if liquidity_ratio < 3:
            score -= 15

    return max(score, 0)
