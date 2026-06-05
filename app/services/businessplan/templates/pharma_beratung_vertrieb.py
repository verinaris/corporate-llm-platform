"""
Pharma-Beratung & Vertrieb — Branchen-Vorlage.

Realistische Defaults für eine Beratungs- und Vertriebs-Boutique im Pharma-Umfeld:
- Beratung: Regulatory Affairs, Pharmakovigilanz, MedDev, Compliance-Audits
- Vertrieb: Außendienst-Unterstützung, CRM-Strategie, Multichannel-Marketing

Compliance-Tiefe: **Mittel** — Begriffe und Rahmen genannt, keine
Paragrafen-genauen Aussagen (juristische Tiefe gehört in den Anwalts-Termin).
"""

from app.services.businessplan.models import BusinessPlanInput, TemplateInfo


INFO = TemplateInfo(
    id="pharma_beratung_vertrieb",
    name="Pharma-Beratung & Vertrieb",
    description=(
        "Vorlage für eine Beratungs- und Vertriebs-Boutique im Pharma-Umfeld. "
        "Inklusive Hinweise zu HWG, AMG, FSA-Kodex, DSGVO Art. 9 und EU AI Act. "
        "Compliance-Tiefe: Mittel — zeigt, dass die richtigen Fragen gestellt werden."
    ),
    industry="pharma_beratung_vertrieb",
    is_example=False,
)


def get_default_input() -> BusinessPlanInput:
    """
    Defaults für Pharma-Beratung + Vertrieb.

    Werte basieren auf typischen KMU-Boutiquen (3-15 MA, hochpreisige Mandate
    bei Compliance-Knappheit).
    """
    return BusinessPlanInput(
        startup_name="Pharma Consult & Sales",
        legal_form="GmbH (empfohlen wegen Haftung)",
        founder_name="",
        location="",
        template_id="pharma_beratung_vertrieb",
        industry="pharma_beratung_vertrieb",

        mission=(
            "Wir verbinden regulatorische Sicherheit mit datengetriebenem "
            "Vertrieb für Pharma-Unternehmen im Mittelstand und Generika-Bereich."
        ),
        problem=(
            "Pharma-Unternehmen stehen unter doppeltem Druck: regulatorische "
            "Anforderungen (HWG, AMG, FSA-Kodex, EU AI Act) werden komplexer, "
            "gleichzeitig erwartet der Außendienst moderne, datenbasierte "
            "Werkzeuge. Spezialisierte Beratung ist knapp und teuer; "
            "interne Aufbau-Versuche scheitern oft an fehlender Pharma-Tiefe."
        ),
        solution=(
            "Beratungs- und Vertriebs-Boutique mit zwei verzahnten Säulen: "
            "(1) Regulatorische Beratung für Werbeaussagen, AMG-Konformität, "
            "Pharmakovigilanz-Prozesse und KI-Risikoklassifizierung. "
            "(2) Vertriebs-Unterstützung mit HCP-konformer Außendienst-Vorbereitung, "
            "CRM-Strategie und HWG-konformer Multichannel-Kommunikation. "
            "Lokal betreibbare KI-Werkzeuge sorgen für Datenhoheit bei "
            "patienten- und praxisnahen Daten."
        ),
        usp=(
            "Wir sind keine reinen Juristen und keine reinen Vertriebler — "
            "wir verbinden beide Welten, sprechen die Sprache der MSL/RA und "
            "der Außendienst-Leitung. Lokal hostbare KI-Tools für Daten mit "
            "Art. 9 DSGVO-Bezug. Audit-fähige Dokumentation aller Empfehlungen."
        ),
        target_customers=(
            "Mittelständische Pharma-Unternehmen (Generika, Specialty Pharma, "
            "MedTech) ohne eigene Compliance-Abteilung. Marketing-Manager mit "
            "neuen Indikations-Kampagnen. Außendienst-Leiter, die Reps "
            "HWG-konform digital ausstatten wollen. CDMO/CMOs vor Audits."
        ),
        revenue_model=(
            "Drei Säulen: (1) Tagesätze für Beratungsmandate (1.200–1.800 €/Tag). "
            "(2) Retainer-Verträge ab 2.500 €/Monat für laufende Begleitung. "
            "(3) Vertriebs-Tooling als Software-Plus-Service (Setup + monatlicher "
            "Support). Ausführliche Audits/Schulungen als Festpreis-Pakete."
        ),
        pricing_basic=799.0,       # Retainer light (Q&A, Newsletter)
        pricing_pro=2500.0,        # Vollständiger Compliance-Retainer
        pricing_enterprise=6500.0, # Inkl. Außendienst-Tooling
        expected_customers_year1=6,    # Realistisch: lange Sales-Zyklen
        expected_customers_year2=15,
        expected_customers_year3=30,
        average_monthly_revenue_per_customer=2800.0,  # höher als KMU-Standard
        setup_fee_average=8500.0,                     # Audit + Onboarding

        founder_equity=20000.0,
        required_capital=80000.0,         # Höher: Compliance-Toolchain, Anwalt im Beirat
        monthly_fixed_costs=6500.0,        # Höher: Anwalt-Beirat, Versicherung, Tools
        marketing_budget_year1=18000.0,    # Branchen-Messen, FSA-Veranstaltungen
        development_budget_year1=22000.0,  # Tooling-Setup (lokal hostbare KI-Plattform)

        sales_channels=(
            "Direkter Vertrieb über DPhG/BPI-Netzwerk. LinkedIn (Pharma-RA-/MSL-Gruppen). "
            "Veröffentlichungen in Pharma-Marketing-Journals. "
            "Vorträge bei FSA-Veranstaltungen, BPI-Arbeitskreisen. "
            "Empfehlungs-Partnerschaften mit Pharma-Anwaltskanzleien und CROs."
        ),

        compliance_status=(
            "Beratungsmandant berücksichtigt HWG (Werbeaussagen-Filter, "
            "keine Superlative, Pflichtangaben), AMG (Zulassungs-Bezug), "
            "FSA-Kodex (HCP-Interaktion). Datenschutz: DSGVO mit Schwerpunkt "
            "Art. 9 (Gesundheitsdaten), AVV-Vorlagen vorhanden. "
            "KI-Einsatz: EU AI Act Risikoklassifizierung wird pro Use-Case "
            "geprüft; patienten-/praxisnahe Verarbeitung nur via lokal "
            "hostbarer Modelle (Ollama-Stack). Pharmakovigilanz-Meldepfade "
            "im Beratungs-Workflow vorgesehen. Audit-Trail-Retention 10 Jahre."
        ),

        risks=(
            "Lange B2B-Vertriebszyklen (6-12 Monate). Personenabhängigkeit "
            "(Schlüssel-Beziehungen). Regulatorische Verschiebungen "
            "(EU AI Act, HWG-Reformen) können Beratungs-Profile entwerten. "
            "Reputations-Risiko bei fehlerhaften Compliance-Empfehlungen — "
            "Haftpflicht-Versicherung Pflicht. Pharmakovigilanz-Meldepflichten "
            "und 10-Jahres-Aufbewahrung erfordern stabile IT. Hyperscaler-Tools "
            "für Pharma erzeugen Druck auf Tagesätze."
        ),
        region="DE",
    )
