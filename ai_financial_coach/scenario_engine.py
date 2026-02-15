import numpy as np

def forecast_cash_flow(income, expenses, growth_rate=0.05, years=5):
    forecast = []
    for year in range(years):
        income *= (1 + growth_rate)
        forecast.append(income - expenses)
    return forecast


def simulate_scenario(income, expenses, scenario):
    if scenario == "Job Loss":
        return -expenses
    if scenario == "Salary Hike":
        return income * 1.3 - expenses
    if scenario == "New Loan":
        return income - (expenses + 5000)
    return income - expenses
