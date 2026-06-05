"""
Verinaris — Beispiel-Vorlage.

Konkret ausgefüllte Vorlage für die geplante Firma 'Verinaris' (Sascha Kern,
Koblenz). Dient als Anschauungs-Beispiel für die Plattform-Nutzer:
"So sieht ein gut ausgefüllter Plan aus."

Werte aus dem ursprünglichen Verinaris-MVP übernommen.
"""

from app.services.businessplan.models import BusinessPlanInput, TemplateInfo


INFO = TemplateInfo(
    id="verinaris_beispiel",
    name="Verinaris (Beispiel)",
    description=(
        "Beispiel-Plan einer KI-Plattform für regulierte KMU. Zeigt, wie ein "
        "vollständig ausgefüllter, bankentauglicher Plan im Datenschutz- und "
        "KI-Kontext aussieht. Nützlich als Referenz."
    ),
    industry="ki_consulting",
    is_example=True,
)


def get_default_input() -> BusinessPlanInput:
    """Gibt die Verinaris-Beispieldaten zurück."""
    return BusinessPlanInput(
        startup_name="Verinaris",
        legal_form="Einzelunternehmen / UG / GmbH offen",
        founder_name="Sascha Kern",
        location="Koblenz, Rheinland-Pfalz",
        template_id="verinaris_beispiel",
        mission=(
            "Rechtskonforme, lokal betreibbare Corporate-LLM-Lösung für KMU."
        ),
        problem=(
            "Viele Organisationen wollen KI nutzen, dürfen sensible Daten "
            "aber nicht unkontrolliert in externe Systeme geben."
        ),
        solution=(
            "Verinaris bietet eine lokale oder EU-hostbare KI-Plattform "
            "für Dokumentenanalyse, Wissensarbeit und Anforderungsmanagement."
        ),
        usp=(
            "Datenhoheit, EU-AI-Act-/DSGVO-Fokus, lokale Betriebsoption "
            "und KMU-taugliche Umsetzung."
        ),
        target_customers=(
            "KMU, Kanzleien, Beratungen, Behörden, Coaches und "
            "regulierte Organisationen."
        ),
        revenue_model=(
            "Lizenzmodell, Setup-Pauschale, Supportvertrag und "
            "optionale Beratung."
        ),
        pricing_basic=249.0,
        pricing_pro=699.0,
        pricing_enterprise=1490.0,
        expected_customers_year1=10,
        expected_customers_year2=30,
        expected_customers_year3=70,
        average_monthly_revenue_per_customer=650.0,
        setup_fee_average=2500.0,
        founder_equity=15000.0,
        required_capital=60000.0,
        monthly_fixed_costs=4200.0,
        marketing_budget_year1=12000.0,
        development_budget_year1=25000.0,
        sales_channels=(
            "Direktvertrieb, LinkedIn, Partner-Netzwerke, "
            "IHK-/HWK-Veranstaltungen, Datenschutz- und IT-Berater."
        ),
        compliance_status=(
            "Konzeptphase; TOMs, AVV, Löschkonzept und "
            "Risikoklassifizierung werden aufgebaut."
        ),
        risks=(
            "Lange Vertriebszyklen, Vertrauen, regulatorische Änderungen, "
            "starke Wettbewerber, technischer Betriebsaufwand."
        ),
        region="RP",  # Rheinland-Pfalz → ISB-Förderung im Matching
    )
