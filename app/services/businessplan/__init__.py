"""
Businessplan-Service — branchenübergreifender Businessplan-Generator.

**Architektur-Idee:**
- `models.py`     — Pydantic-Schemas + DB-Modell (BusinessPlan)
- `financials.py` — 3-Jahres-Forecast (regelbasiert)
- `checks.py`     — Härtungs-Checks IHK/HwK/Bank/BA/Compliance/Vertrieb
- `funding.py`    — Fördermittel-Matching (mit Regional-Filter)
- `scoring.py`    — 4-KPI-Scorecard
- `summary.py`    — LLM-Executive-Summary (Anthropic ODER Ollama)
- `templates/`    — Branchen-Vorlagen (KMU, Verinaris, ggf. Pharma, Anwalt...)
- `export/`       — Word/Excel/PDF Generierung

**Verglichen mit dem Verinaris-MVP:**
- Statt monolithischer Streamlit-App → saubere Service-Schicht
- Statt eigener Ollama-Anbindung → unsere Provider-Abstraktion
- Statt hardcoded Daten → Template-System
- Statt eigener Auth/DB → Plattform-Auth + zentrale DB
"""

from app.services.businessplan.models import (
    BusinessPlan,
    BusinessPlanInput,
    BusinessPlanResult,
    BusinessPlanSummary,
    CheckResult,
    FinancialYear,
    FundingMatch,
    ScoreCard,
    TemplateInfo,
)
from app.services.businessplan.financials import calculate_financials
from app.services.businessplan.checks import run_hardening_checks
from app.services.businessplan.industry_checks import run_industry_checks
from app.services.businessplan.funding import find_funding_matches
from app.services.businessplan.scoring import score_plan
from app.services.businessplan.summary import generate_executive_summary
from app.services.businessplan.templates import (
    get_template_default,
    get_template_info,
    list_templates,
)


async def generate_business_plan(
    p: BusinessPlanInput,
    llm_model: str | None = None,
) -> BusinessPlanResult:
    """
    Hauptfunktion: Erzeugt aus Input einen vollständigen BusinessPlanResult.

    Workflow:
    1. Finanz-Forecast
    2. Generische Härtungs-Checks
    3. Branchen-spezifische Checks (z.B. Pharma · HWG, DSGVO Art. 9)
    4. Fördermittel-Matching (inkl. branchen-spezifischer Programme)
    5. Score-Berechnung über ALLE Checks
    6. Executive Summary via LLM (oder Fallback)

    Args:
        p: Eingaben (User-Formular)
        llm_model: Modell für die Summary (None = regelbasierter Fallback)
    """
    financials = calculate_financials(p)
    generic_checks = run_hardening_checks(p, financials)
    industry_checks = run_industry_checks(p, financials)
    checks = generic_checks + industry_checks
    funding = find_funding_matches(p)
    scores = score_plan(checks)
    summary, llm_used = await generate_executive_summary(p, checks, model=llm_model)

    return BusinessPlanResult(
        input=p,
        financials=financials,
        checks=checks,
        funding=funding,
        scores=scores,
        summary=summary,
        llm_used=llm_used,
    )


__all__ = [
    # Schemas
    "BusinessPlan",
    "BusinessPlanInput",
    "BusinessPlanResult",
    "BusinessPlanSummary",
    "CheckResult",
    "FinancialYear",
    "FundingMatch",
    "ScoreCard",
    "TemplateInfo",
    # Sub-Services
    "calculate_financials",
    "run_hardening_checks",
    "run_industry_checks",
    "find_funding_matches",
    "score_plan",
    "generate_executive_summary",
    # Templates
    "list_templates",
    "get_template_default",
    "get_template_info",
    # Orchestrator
    "generate_business_plan",
]
