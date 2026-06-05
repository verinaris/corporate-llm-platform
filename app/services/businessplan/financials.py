"""
Finanzberechnung für den Businessplan (3-Jahres-Forecast).

Logik aus dem Verinaris-MVP übernommen, aber refaktoriert:
- Pure Funktion, keine Streamlit-Abhängigkeit
- Klare Typen (Pydantic)
- Testbar in Isolation
"""

from app.services.businessplan.models import (
    BusinessPlanInput,
    FinancialYear,
)


def calculate_financials(p: BusinessPlanInput) -> list[FinancialYear]:
    """
    Berechnet einen 3-Jahres-Forecast.

    Annahmen (wie im Verinaris-MVP):
    - Fixkosten steigen um 8% pro Jahr
    - Marketing steigt um 25% pro Jahr
    - Entwicklungskosten sinken: Jahr 2 = 75%, Jahr 3 = 55% des Initials
    """
    customers_per_year = [
        p.expected_customers_year1,
        p.expected_customers_year2,
        p.expected_customers_year3,
    ]
    development_factors = [1.0, 0.75, 0.55]

    result: list[FinancialYear] = []

    for idx, customers in enumerate(customers_per_year):
        year = idx + 1
        recurring = customers * p.average_monthly_revenue_per_customer * 12
        setup = customers * p.setup_fee_average
        total_revenue = recurring + setup

        fixed = p.monthly_fixed_costs * 12 * (1 + 0.08 * (year - 1))
        marketing = p.marketing_budget_year1 * (1 + 0.25 * (year - 1))
        development = p.development_budget_year1 * development_factors[idx]
        total_costs = fixed + marketing + development

        result.append(
            FinancialYear(
                year=year,
                customers=customers,
                recurring_revenue=round(recurring, 2),
                setup_revenue=round(setup, 2),
                total_revenue=round(total_revenue, 2),
                fixed_costs=round(fixed, 2),
                marketing=round(marketing, 2),
                development=round(development, 2),
                total_costs=round(total_costs, 2),
                profit_before_tax=round(total_revenue - total_costs, 2),
            )
        )

    return result
