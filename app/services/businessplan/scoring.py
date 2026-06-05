"""
Score-Berechnung aus den Härtungs-Checks.

4 KPIs:
- Businessplan-Reifegrad (allgemein)
- Bankenfähigkeit (strenger)
- Förderfähigkeit (etwas wohlwollender)
- Investorenfähigkeit (am strengsten — VCs sind hart)
"""

from app.services.businessplan.models import CheckResult, ScoreCard


# Strafen pro Status (Verinaris-MVP-Logik beibehalten)
_PENALTIES = {
    "OK": 0,
    "Nachschärfen": 8,
    "Kritisch": 18,
}


def score_plan(checks: list[CheckResult]) -> ScoreCard:
    """
    Berechnet 4 Score-Werte basierend auf den Check-Ergebnissen.

    Annahmen:
    - Banken sind ~4 Punkte strenger als allgemeiner Reifegrad
    - Fördermittel sind ~5 Punkte wohlwollender
    - VCs sind ~12 Punkte strenger
    - Untergrenze 20-30, damit auch schwache Pläne nicht bei 0% landen
    """
    if not checks:
        # Keine Checks = neutral
        return ScoreCard(
            business_plan_maturity=50,
            bankability=46,
            fundability=55,
            investability=38,
        )

    total_penalty = sum(_PENALTIES.get(c.status, 8) for c in checks)
    base_score = max(30, 100 - total_penalty)

    return ScoreCard(
        business_plan_maturity=base_score,
        bankability=max(25, base_score - 4),
        fundability=min(95, base_score + 5),
        investability=max(20, base_score - 12),
    )
