"""Tests für den Businessplan-Generator."""

import pytest

from app.services.businessplan import (
    calculate_financials,
    find_funding_matches,
    generate_business_plan,
    get_template_default,
    list_templates,
    run_hardening_checks,
    score_plan,
)
from app.services.businessplan.models import BusinessPlanInput
from app.services.businessplan.export import export_docx, export_pdf, export_xlsx


# ============================================================ #
# Templates
# ============================================================ #

def test_templates_listed():
    templates = list_templates()
    ids = [t.id for t in templates]
    assert "kmu_default" in ids
    assert "verinaris_beispiel" in ids


def test_kmu_default_is_loadable():
    bp = get_template_default("kmu_default")
    assert isinstance(bp, BusinessPlanInput)
    assert bp.template_id == "kmu_default"


def test_verinaris_template_has_realistic_data():
    bp = get_template_default("verinaris_beispiel")
    assert bp.startup_name == "Verinaris"
    assert bp.region == "RP"
    assert bp.required_capital >= 50000


def test_unknown_template_falls_back_to_kmu():
    bp = get_template_default("does-not-exist")
    assert bp.template_id == "kmu_default"


# ============================================================ #
# Finanzen
# ============================================================ #

def test_financials_three_years():
    bp = get_template_default("verinaris_beispiel")
    fin = calculate_financials(bp)
    assert len(fin) == 3
    assert fin[0].year == 1
    assert fin[2].year == 3


def test_financials_growing_customers():
    bp = get_template_default("verinaris_beispiel")
    fin = calculate_financials(bp)
    # Kundenwachstum sollte sich in steigendem Umsatz spiegeln
    assert fin[2].total_revenue > fin[0].total_revenue


def test_financials_zero_customers():
    """Edge: 0 Kunden → kein Umsatz aber Kosten."""
    bp = BusinessPlanInput(
        startup_name="Test",
        expected_customers_year1=0,
        expected_customers_year2=0,
        expected_customers_year3=0,
    )
    fin = calculate_financials(bp)
    assert fin[0].total_revenue == 0
    assert fin[0].profit_before_tax < 0  # Verlust


# ============================================================ #
# Härtungs-Checks
# ============================================================ #

def test_hardening_checks_returns_all_areas():
    bp = get_template_default("verinaris_beispiel")
    fin = calculate_financials(bp)
    checks = run_hardening_checks(bp, fin)
    areas = {c.area for c in checks}
    # Wir erwarten mind. diese Bereiche
    assert "IHK/HwK" in areas
    assert "Bank" in areas
    assert "BA" in areas
    assert "Compliance" in areas
    assert "Vertrieb" in areas


def test_check_critical_when_missing_idea():
    bp = BusinessPlanInput(
        startup_name="Leerplan",
        problem="",
        solution="",
        target_customers="",
    )
    fin = calculate_financials(bp)
    checks = run_hardening_checks(bp, fin)
    ihk = next(c for c in checks if c.area == "IHK/HwK")
    assert ihk.status == "Kritisch"


def test_check_bank_equity_ok_when_high():
    bp = BusinessPlanInput(
        startup_name="Test",
        founder_equity=50000,
        required_capital=50000,  # 100% Eigenkapital
        monthly_fixed_costs=3000,
    )
    fin = calculate_financials(bp)
    checks = run_hardening_checks(bp, fin)
    bank_checks = [c for c in checks if c.area == "Bank"]
    # Eigenkapital-Check (erster Bank-Check) sollte OK sein
    assert bank_checks[0].status == "OK"


# ============================================================ #
# Fördermittel
# ============================================================ #

def test_funding_includes_federal_programs():
    bp = get_template_default("kmu_default")
    funds = find_funding_matches(bp)
    names = [f.name for f in funds]
    assert any("KfW" in n for n in names)
    assert any("BAFA" in n for n in names)


def test_funding_includes_regional_for_rp():
    bp = get_template_default("verinaris_beispiel")  # region=RP
    funds = find_funding_matches(bp)
    names = [f.name for f in funds]
    assert any("ISB" in n for n in names)


def test_funding_excludes_regional_for_de_only():
    bp = BusinessPlanInput(startup_name="X", region="DE")
    funds = find_funding_matches(bp)
    names = [f.name for f in funds]
    assert not any("ISB" in n for n in names)


# ============================================================ #
# Scoring
# ============================================================ #

def test_score_in_valid_range():
    bp = get_template_default("verinaris_beispiel")
    fin = calculate_financials(bp)
    checks = run_hardening_checks(bp, fin)
    scores = score_plan(checks)
    assert 0 <= scores.business_plan_maturity <= 100
    assert 0 <= scores.bankability <= 100
    assert 0 <= scores.fundability <= 100
    assert 0 <= scores.investability <= 100


def test_score_investability_strictest():
    """Investorenfähigkeit sollte tendenziell am niedrigsten sein."""
    bp = get_template_default("kmu_default")
    fin = calculate_financials(bp)
    checks = run_hardening_checks(bp, fin)
    scores = score_plan(checks)
    # Investability ist meist <= bankability
    assert scores.investability <= scores.bankability + 1


# ============================================================ #
# Orchestrator
# ============================================================ #

@pytest.mark.asyncio
async def test_generate_business_plan_without_llm():
    """Orchestrator funktioniert auch ohne LLM (Fallback-Summary)."""
    bp = get_template_default("kmu_default")
    result = await generate_business_plan(bp, llm_model=None)
    assert result.input.startup_name == bp.startup_name
    assert len(result.financials) == 3
    assert len(result.checks) >= 5
    assert result.scores.business_plan_maturity > 0
    assert result.summary  # nicht leer
    assert result.llm_used == "rule-based"


# ============================================================ #
# Exports
# ============================================================ #

@pytest.mark.asyncio
async def test_docx_export_produces_bytes():
    bp = get_template_default("verinaris_beispiel")
    result = await generate_business_plan(bp, llm_model=None)
    data = export_docx(result)
    # DOCX-Magic: ZIP-Header beginnt mit 'PK'
    assert data[:2] == b"PK"
    assert len(data) > 1000


@pytest.mark.asyncio
async def test_xlsx_export_produces_bytes():
    bp = get_template_default("verinaris_beispiel")
    result = await generate_business_plan(bp, llm_model=None)
    data = export_xlsx(result)
    # XLSX-Magic: ZIP-Header beginnt mit 'PK'
    assert data[:2] == b"PK"
    assert len(data) > 1000


@pytest.mark.asyncio
async def test_pdf_export_produces_bytes():
    bp = get_template_default("verinaris_beispiel")
    result = await generate_business_plan(bp, llm_model=None)
    data = export_pdf(result)
    # PDF-Magic
    assert data[:4] == b"%PDF"
    assert len(data) > 500


# ============================================================ #
# Phase 5b — Pharma-Template + Industry-Checks
# ============================================================ #

def test_pharma_template_registered():
    """Pharma-Vorlage taucht in der Registry auf."""
    templates = list_templates()
    ids = [t.id for t in templates]
    assert "pharma_beratung_vertrieb" in ids


def test_pharma_template_has_industry_set():
    """Pharma-Default hat industry=pharma_beratung_vertrieb."""
    bp = get_template_default("pharma_beratung_vertrieb")
    assert bp.industry == "pharma_beratung_vertrieb"
    assert bp.template_id == "pharma_beratung_vertrieb"


def test_pharma_template_has_realistic_pricing():
    """Pharma-Preise sind höher als KMU-Standard."""
    pharma = get_template_default("pharma_beratung_vertrieb")
    kmu = get_template_default("kmu_default")
    assert pharma.pricing_pro > kmu.pricing_pro
    assert pharma.setup_fee_average > kmu.setup_fee_average


def test_pharma_industry_checks_run():
    """Industry-Checks für Pharma laufen und liefern Ergebnisse."""
    from app.services.businessplan.industry_checks import run_industry_checks
    bp = get_template_default("pharma_beratung_vertrieb")
    fin = calculate_financials(bp)
    industry_checks = run_industry_checks(bp, fin)

    # Mind. 3 Pharma-Checks erwartet (HWG, DSGVO Art. 9, Pharmakovigilanz)
    assert len(industry_checks) >= 3

    areas = {c.area for c in industry_checks}
    assert any("HWG" in a for a in areas)
    assert any("Pharmakovigilanz" in a for a in areas)


def test_industry_checks_empty_for_generic():
    """Generische Branche → keine industry-spezifischen Checks."""
    from app.services.businessplan.industry_checks import run_industry_checks
    bp = get_template_default("kmu_default")
    fin = calculate_financials(bp)
    industry_checks = run_industry_checks(bp, fin)
    assert industry_checks == []


def test_hwg_critical_language_detection():
    """HWG-Filter erkennt verbotene Superlative."""
    from app.services.businessplan.industry_checks import (
        _contains_hwg_critical_language,
    )
    assert _contains_hwg_critical_language("Wir sind die Besten am Markt")
    assert _contains_hwg_critical_language("Garantiert nebenwirkungsfrei")
    assert _contains_hwg_critical_language("Heilt zu 100%")
    # Sauberer Text sollte nichts triggern
    assert not _contains_hwg_critical_language(
        "Wir beraten Mittelstandskunden in Compliance-Fragen."
    )


def test_pharma_hwg_check_triggers_on_superlatives():
    """Wenn Plan-Text Superlative enthält → HWG-Check schlägt an."""
    from app.services.businessplan.industry_checks import run_industry_checks
    bp = get_template_default("pharma_beratung_vertrieb")
    bp.usp = "Wir sind die einzigartige Lösung garantiert nebenwirkungsfrei"
    fin = calculate_financials(bp)
    checks = run_industry_checks(bp, fin)
    hwg_check = next(c for c in checks if c.area == "Pharma · HWG")
    assert hwg_check.status == "Nachschärfen"


def test_pharma_funding_includes_industry_programs():
    """Pharma-Plan bekommt zusätzlich KMU-innovativ + ZIM."""
    from app.services.businessplan import find_funding_matches
    bp = get_template_default("pharma_beratung_vertrieb")
    funds = find_funding_matches(bp)
    names = [f.name for f in funds]
    assert any("KMU-innovativ" in n for n in names)
    assert any("ZIM" in n for n in names)


def test_pharma_funding_does_not_leak_to_generic():
    """KMU-Default-Plan bekommt KEINE Pharma-Programme."""
    from app.services.businessplan import find_funding_matches
    bp = get_template_default("kmu_default")
    funds = find_funding_matches(bp)
    names = [f.name for f in funds]
    assert not any("KMU-innovativ: Medizintechnik" in n for n in names)


@pytest.mark.asyncio
async def test_pharma_full_plan_integrates_industry_checks():
    """End-to-End: Pharma-Plan enthält generic + industry Checks."""
    bp = get_template_default("pharma_beratung_vertrieb")
    result = await generate_business_plan(bp, llm_model=None)

    # Generische Checks (IHK/Bank/BA/Compliance/Vertrieb) + Pharma-Checks
    areas = {c.area for c in result.checks}
    # Generic
    assert "IHK/HwK" in areas
    assert "Bank" in areas
    # Pharma-spezifisch
    assert any("Pharma" in a for a in areas)
