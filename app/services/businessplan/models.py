"""
Pydantic-Schemas + DB-Modell für den Businessplan-Generator (Phase 5+).

Das Schema ist branchenübergreifend gestaltet. Branchenspezifische
Vorbelegungen kommen aus `templates/` und füllen nur die Defaults.

Alle monetären Werte: EUR (Achtung: token-tracker rechnet weiter in USD —
das ist OK, sind unterschiedliche Domänen).
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


# ============================================================ #
# Eingabe-Schema (was der User ausfüllt)
# ============================================================ #

class BusinessPlanInput(BaseModel):
    """Vollständiges Eingabe-Schema für einen Businessplan."""

    # --- Unternehmen ---
    startup_name: str = Field(..., min_length=1, max_length=200)
    legal_form: str = Field(default="Einzelunternehmen / UG / GmbH offen")
    founder_name: str = Field(default="")
    location: str = Field(default="")
    template_id: str = Field(
        default="kmu_default",
        description="Welche Branchen-Vorlage zugrunde liegt",
    )

    # --- Geschäftsidee ---
    mission: str = Field(default="", max_length=2000)
    problem: str = Field(default="", max_length=2000)
    solution: str = Field(default="", max_length=2000)
    usp: str = Field(default="", max_length=2000)
    target_customers: str = Field(default="", max_length=2000)
    revenue_model: str = Field(default="", max_length=2000)

    # --- Preise (€/Monat) ---
    pricing_basic: float = Field(default=99.0, ge=0)
    pricing_pro: float = Field(default=299.0, ge=0)
    pricing_enterprise: float = Field(default=999.0, ge=0)

    # --- Kundenwachstum ---
    expected_customers_year1: int = Field(default=10, ge=0)
    expected_customers_year2: int = Field(default=25, ge=0)
    expected_customers_year3: int = Field(default=60, ge=0)
    average_monthly_revenue_per_customer: float = Field(default=400.0, ge=0)
    setup_fee_average: float = Field(default=1500.0, ge=0)

    # --- Finanzierung & Kosten (EUR) ---
    founder_equity: float = Field(default=15000.0, ge=0)
    required_capital: float = Field(default=50000.0, ge=0)
    monthly_fixed_costs: float = Field(default=3500.0, ge=0)
    marketing_budget_year1: float = Field(default=10000.0, ge=0)
    development_budget_year1: float = Field(default=20000.0, ge=0)

    # --- Strategie ---
    sales_channels: str = Field(default="", max_length=2000)
    compliance_status: str = Field(default="", max_length=2000)
    risks: str = Field(default="", max_length=2000)

    # --- Optional: Standort-Region (für Fördermittel-Matching) ---
    region: str = Field(
        default="DE",
        description="DE oder Bundesland-Kürzel (RP, BY, BW, NRW, ...) für regionale Fördermittel",
    )

    # --- Optional: Branche (für branchen-spezifische Checks + Fördermittel) ---
    industry: str = Field(
        default="generic",
        description=(
            "Branche: 'generic', 'pharma_beratung_vertrieb', 'ki_consulting', ... "
            "Wird i.d.R. aus Template übernommen."
        ),
    )

    @field_validator("region")
    @classmethod
    def _validate_region(cls, v: str) -> str:
        return v.strip().upper()[:10] or "DE"


# ============================================================ #
# Ergebnis-Schema (was berechnet wird)
# ============================================================ #

class FinancialYear(BaseModel):
    """Eine Jahres-Zeile im Finanzmodell."""

    year: int
    customers: int
    recurring_revenue: float
    setup_revenue: float
    total_revenue: float
    fixed_costs: float
    marketing: float
    development: float
    total_costs: float
    profit_before_tax: float


class CheckResult(BaseModel):
    """Eine einzelne Härtungs-Prüfung."""

    area: str  # IHK/HwK, Bank, BA, Compliance, Vertrieb
    status: str  # OK, Nachschärfen, Kritisch
    finding: str
    recommendation: str


class FundingMatch(BaseModel):
    """Ein Fördermittel-Treffer."""

    name: str
    fit: str  # Niedrig, Mittel, Hoch
    why: str
    next_step: str
    region: Optional[str] = None
    url: Optional[str] = None


class ScoreCard(BaseModel):
    """Die berechneten Scores."""

    business_plan_maturity: int = Field(ge=0, le=100)
    bankability: int = Field(ge=0, le=100)
    fundability: int = Field(ge=0, le=100)
    investability: int = Field(ge=0, le=100)


class BusinessPlanResult(BaseModel):
    """Vollständiges Ergebnis: alles was nach Berechnung verfügbar ist."""

    input: BusinessPlanInput
    financials: list[FinancialYear]
    checks: list[CheckResult]
    funding: list[FundingMatch]
    scores: ScoreCard
    summary: str = Field(description="Executive Summary (Text)")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    llm_used: Optional[str] = Field(
        default=None,
        description="Welches LLM die Summary erzeugt hat (oder 'rule-based')",
    )


# ============================================================ #
# Vorlagen-Metadaten
# ============================================================ #

class TemplateInfo(BaseModel):
    """Beschreibt eine Branchen-Vorlage."""

    id: str  # z.B. "kmu_default", "verinaris_beispiel"
    name: str  # User-friendly: "KMU Standard"
    description: str
    industry: str  # generic, pharma, legal, tax, ...
    is_example: bool = False  # True wenn Beispiel-Plan (Verinaris)


# ============================================================ #
# DB-Modell (gespeicherte Pläne)
# ============================================================ #

class BusinessPlan(SQLModel, table=True):
    """
    Gespeicherter Businessplan in der zentralen DB.

    Speichert das gesamte Input-Schema als JSON. So bleiben Pläne auch
    nach Schema-Erweiterungen lesbar (älter zuverlässig, neuer mit
    fehlenden Feldern = Defaults).
    """

    __tablename__ = "business_plans"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_email: str = SQLField(index=True)
    name: str  # = startup_name beim Speichern
    template_id: str = SQLField(default="kmu_default", index=True)
    input_json: str  # serialisiertes BusinessPlanInput
    last_score: int = SQLField(default=0)  # für schnelle Listen-Anzeige
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================ #
# API-Response für Plan-Listung
# ============================================================ #

class BusinessPlanSummary(BaseModel):
    """Kurz-Info für Plan-Listen (ohne Volldaten)."""

    id: int
    name: str
    template_id: str
    last_score: int
    created_at: datetime
    updated_at: datetime
