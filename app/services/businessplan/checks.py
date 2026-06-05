"""
Härtungs-Checks gegen IHK/HwK/Bank/BA-Anforderungen.

Regel-basierte Prüfung — bewusst KEINE LLM-Logik, weil hier
Reproduzierbarkeit für Banken/Behörden wichtig ist.

Aus Verinaris-MVP übernommen, erweitert und in Pure-Functions refaktoriert.
"""

from app.services.businessplan.models import (
    BusinessPlanInput,
    CheckResult,
    FinancialYear,
)


def run_hardening_checks(
    p: BusinessPlanInput,
    financials: list[FinancialYear],
) -> list[CheckResult]:
    """
    Führt 5 Prüfbereiche durch:
    1. IHK/HwK — Geschäftsidee vollständig?
    2. Bank — Eigenkapital + Liquidität?
    3. BA — Tragfähigkeit (Jahr-1-Profit)?
    4. Compliance — DSGVO/AI-Act vorbereitet?
    5. Vertrieb — Kanäle + Budget belastbar?
    """
    checks: list[CheckResult] = []

    equity_ratio = p.founder_equity / max(p.required_capital, 1)
    year1_profit = financials[0].profit_before_tax if financials else 0.0
    liquidity_months = p.founder_equity / max(p.monthly_fixed_costs, 1)

    # 1. IHK/HwK — Geschäftsidee
    idea_complete = bool(p.problem) and bool(p.solution) and bool(p.target_customers)
    checks.append(
        CheckResult(
            area="IHK/HwK",
            status="OK" if idea_complete else "Kritisch",
            finding=(
                "Geschäftsidee, Zielgruppe und Nutzenversprechen sind beschrieben."
                if idea_complete
                else "Kernlogik der Geschäftsidee ist unvollständig."
            ),
            recommendation=(
                "Problem, Lösung, Zielgruppe und Kundennutzen auf max. 1 Seite präzisieren."
            ),
        )
    )

    # 2a. Bank — Eigenkapitalquote
    checks.append(
        CheckResult(
            area="Bank",
            status="OK" if equity_ratio >= 0.2 else "Nachschärfen",
            finding=f"Eigenkapitalquote liegt bei {equity_ratio:.0%}.",
            recommendation=(
                "Mindestens 20% Eigenkapital empfohlen. "
                "Sonst: Eigenkapital, Fördermittel oder kleinere Startphase prüfen."
            ),
        )
    )

    # 2b. Bank — Liquiditätsreserve
    checks.append(
        CheckResult(
            area="Bank",
            status="OK" if liquidity_months >= 3 else "Kritisch",
            finding=(
                f"Liquiditätsreserve deckt ca. {liquidity_months:.1f} Monate Fixkosten."
            ),
            recommendation="Liquiditätspuffer von mindestens 3-6 Monaten einplanen.",
        )
    )

    # 3. BA — Tragfähigkeit
    checks.append(
        CheckResult(
            area="BA",
            status="OK" if year1_profit > 0 else "Nachschärfen",
            finding=f"Jahr-1-Ergebnis vor Steuern: {year1_profit:,.0f} €.",
            recommendation=(
                "Tragfähigkeit über realistische Umsatzannahmen, "
                "Pilotkunden und Referenzen stärken."
            ),
        )
    )

    # 4. Compliance
    compliance_text = p.compliance_status or ""
    is_concept_phase = "konzept" in compliance_text.lower() or not compliance_text
    checks.append(
        CheckResult(
            area="Compliance",
            status="Nachschärfen" if is_concept_phase else "OK",
            finding=(
                compliance_text or "Compliance-Status nicht beschrieben."
            ),
            recommendation=(
                "DSGVO-TOMs, AVV, Löschkonzept, Rollenmodell und "
                "KI-Risikoklassifizierung (EU AI Act) dokumentieren."
            ),
        )
    )

    # 5. Vertrieb
    sales_strong = (
        bool(p.sales_channels)
        and len(p.sales_channels) > 30
        and p.marketing_budget_year1 > 0
    )
    checks.append(
        CheckResult(
            area="Vertrieb",
            status="OK" if sales_strong else "Kritisch",
            finding=(
                "Vertriebskanäle und -budget sind belastbar beschrieben."
                if sales_strong
                else "Vertrieb ist nicht belastbar beschrieben."
            ),
            recommendation=(
                "Pilotkunden, Referenzprozess, Conversion-Annahmen "
                "und Sales-Funnel ergänzen."
            ),
        )
    )

    return checks
