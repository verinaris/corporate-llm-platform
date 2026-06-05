"""
KMU-Standard-Vorlage — der neutrale Default für jeden Businessplan.

Diese Vorlage ist branchen-neutral. Sie liefert sinnvolle Beispieltexte und
realistische Finanzannahmen für einen typischen Mittelstands-Software-Service
(SaaS-artig).
"""

from app.services.businessplan.models import BusinessPlanInput, TemplateInfo


INFO = TemplateInfo(
    id="kmu_default",
    name="KMU Standard",
    description=(
        "Neutrale Standard-Vorlage für einen Businessplan eines kleinen oder "
        "mittelständischen Unternehmens. Sinnvoll als Ausgangspunkt für die "
        "meisten Gründungen."
    ),
    industry="generic",
    is_example=False,
)


def get_default_input() -> BusinessPlanInput:
    """Gibt die Default-Werte für ein KMU zurück (leere Texte zum Befüllen)."""
    return BusinessPlanInput(
        startup_name="Mein Unternehmen",
        legal_form="Einzelunternehmen / UG / GmbH offen",
        founder_name="",
        location="",
        template_id="kmu_default",
        mission=(
            "Wir lösen ein konkretes Problem unserer Zielgruppe mit einer "
            "praxisnahen Lösung."
        ),
        problem=(
            "Beschreiben Sie hier kurz: Welches konkrete Problem haben Ihre "
            "zukünftigen Kunden, das Sie adressieren?"
        ),
        solution=(
            "Beschreiben Sie hier: Wie löst Ihr Angebot das Problem? "
            "Welche Form hat Ihr Produkt / Service?"
        ),
        usp=(
            "Was unterscheidet Sie von bestehenden Lösungen? "
            "Was können Sie besser, einfacher, sicherer oder günstiger?"
        ),
        target_customers=(
            "Kleine und mittelständische Unternehmen, "
            "ca. 10–100 Mitarbeitende, in DACH-Region."
        ),
        revenue_model=(
            "Wiederkehrendes Lizenzmodell (Monats- oder Jahresabos) "
            "ergänzt um einmalige Einrichtung und optionale Beratung."
        ),
        pricing_basic=99.0,
        pricing_pro=299.0,
        pricing_enterprise=999.0,
        expected_customers_year1=10,
        expected_customers_year2=25,
        expected_customers_year3=60,
        average_monthly_revenue_per_customer=400.0,
        setup_fee_average=1500.0,
        founder_equity=15000.0,
        required_capital=50000.0,
        monthly_fixed_costs=3500.0,
        marketing_budget_year1=10000.0,
        development_budget_year1=20000.0,
        sales_channels=(
            "Direktvertrieb, LinkedIn, Partner-Netzwerk, "
            "IHK/HWK-Veranstaltungen, branchenspezifische Messen."
        ),
        compliance_status=(
            "DSGVO-Grundlagen vorhanden. AVV-Vorlage erstellt. "
            "TOMs und Löschkonzept in Arbeit."
        ),
        risks=(
            "Lange B2B-Vertriebszyklen, abhängig von Vertrauen "
            "und Referenzen. Hyperscaler-Wettbewerb."
        ),
        region="DE",
    )
