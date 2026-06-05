"""
Fördermittel-Matching für deutsche KMU-Gründungen.

Erweitert das Verinaris-MVP um Regional-Filter (Bundesland) und URLs.
**Wichtig:** Die Liste ist statisch und MUSS vor Antragstellung
tagesaktuell beim jeweiligen Programm geprüft werden.
"""

from app.services.businessplan.models import BusinessPlanInput, FundingMatch


# Föderale Programme — überall verfügbar
_FEDERAL_PROGRAMS: list[FundingMatch] = [
    FundingMatch(
        name="Gründungszuschuss (Bundesagentur für Arbeit)",
        fit="Mittel-Hoch",
        why=(
            "Relevant bei Gründung aus Arbeitslosigkeit (ALG I) mit "
            "tragfähigem Businessplan. 6 Monate Zuschuss zum Lebensunterhalt."
        ),
        next_step=(
            "Tragfähigkeitsbescheinigung von einer fachkundigen Stelle "
            "(z.B. IHK, Steuerberater) einholen."
        ),
        region="DE",
        url="https://www.arbeitsagentur.de/",
    ),
    FundingMatch(
        name="KfW Gründerkredit / ERP-Gründerkredit Universell",
        fit="Mittel",
        why=(
            "Niedrig verzinste Darlehen für Kapitalbedarf, Betriebsmittel "
            "und Investitionen. Bis 25.000 € teilweise ohne Haftung."
        ),
        next_step=(
            "Hausbankgespräch mit ausgearbeiteter Finanzplanung und "
            "3-Jahres-Forecast vorbereiten."
        ),
        region="DE",
        url="https://www.kfw.de/inlandsfoerderung/Unternehmen/Gr%C3%BCnden-Erweitern/",
    ),
    FundingMatch(
        name="BAFA — Förderung für Unternehmensberatung",
        fit="Mittel",
        why=(
            "Bezuschusst Beratungskosten nach der Gründung "
            "(bis zu 50% bzw. 80% in strukturschwachen Regionen)."
        ),
        next_step=(
            "Förderfähigkeit prüfen und nur zugelassene Berater nutzen. "
            "Antrag VOR Beratungsbeginn stellen!"
        ),
        region="DE",
        url="https://www.bafa.de/",
    ),
    FundingMatch(
        name="EXIST-Gründerstipendium",
        fit="Niedrig-Mittel",
        why=(
            "Für innovative, technologieorientierte Gründungen aus "
            "Hochschulen — nur bei Hochschul-Anbindung."
        ),
        next_step="Hochschul-Partner suchen, falls einschlägig.",
        region="DE",
        url="https://www.exist.de/",
    ),
    FundingMatch(
        name="Mittelstand-Digital / regionale KI-Initiativen",
        fit="Mittel",
        why=(
            "Gut für Netzwerk, Pilotierung und Sichtbarkeit. "
            "Selten direkte Produktfinanzierung, aber wertvoll für Referenzen."
        ),
        next_step=(
            "Mittelstand-Digital-Zentrum in der Region kontaktieren."
        ),
        region="DE",
        url="https://www.mittelstand-digital.de/",
    ),
    FundingMatch(
        name="EU Digital Europe / Horizon Europe",
        fit="Niedrig-Mittel",
        why=(
            "Eher für Konsortien, Forschung, Skalierung. "
            "Hoher Antrags-Aufwand — nur bei Partnernetzwerk lohnend."
        ),
        next_step=(
            "Nur bei größerem Vorhaben mit europäischen Partnern verfolgen."
        ),
        region="EU",
        url="https://digital-strategy.ec.europa.eu/",
    ),
]


# Regionale Programme (pro Bundesland — erweitern bei Bedarf)
_REGIONAL_PROGRAMS: dict[str, list[FundingMatch]] = {
    "RP": [
        FundingMatch(
            name="ISB Rheinland-Pfalz — Investitions- und Strukturbank",
            fit="Hoch",
            why=(
                "Landesförderung für Gründer, Start-ups und Wachstum in RLP. "
                "Verschiedene Programme: Mikrokredit RLP, ERP-Startgeld, "
                "Innovationsbürgschaften."
            ),
            next_step=(
                "Aktuelle ISB-Programme (Stand prüfen!) gegen "
                "Investitionsbedarf matchen."
            ),
            region="RP",
            url="https://isb.rlp.de/",
        ),
    ],
    "BY": [
        FundingMatch(
            name="LfA Förderbank Bayern",
            fit="Hoch",
            why="Landesförderung in Bayern für Gründer und Mittelstand.",
            next_step="LfA-Programm-Übersicht gegen Bedarf abgleichen.",
            region="BY",
            url="https://lfa.de/",
        ),
    ],
    "BW": [
        FundingMatch(
            name="L-Bank Baden-Württemberg",
            fit="Hoch",
            why="Landesförderbank BW — Gründerkredite, Innovationsförderung.",
            next_step="L-Bank Förderkompass durcharbeiten.",
            region="BW",
            url="https://www.l-bank.de/",
        ),
    ],
    "NRW": [
        FundingMatch(
            name="NRW.BANK",
            fit="Hoch",
            why="Förderbank NRW — Programme für Gründer, Innovation, Digitalisierung.",
            next_step="NRW.BANK-Kontakt aufnehmen für individuelle Beratung.",
            region="NRW",
            url="https://www.nrwbank.de/",
        ),
    ],
}


# Branchen-spezifische Programme (Pharma, Legal, ...)
_INDUSTRY_PROGRAMS: dict[str, list[FundingMatch]] = {
    "pharma_beratung_vertrieb": [
        FundingMatch(
            name="KMU-innovativ: Medizintechnik (BMBF)",
            fit="Hoch",
            why=(
                "BMBF-Förderung für innovative KMU im Medizintechnik-/Pharma-"
                "Bereich. Auch beratungs- und prozessbezogene Innovationen "
                "förderbar. Stichtage halbjährlich."
            ),
            next_step=(
                "Förderfähigkeit prüfen, Projektskizze vorbereiten. "
                "Beratung beim Projektträger DLR empfohlen."
            ),
            region="DE",
            url="https://www.bmbf.de/bmbf/de/forschung/gesundheit-und-medizin/",
        ),
        FundingMatch(
            name="ZIM (Zentrales Innovationsprogramm Mittelstand)",
            fit="Mittel-Hoch",
            why=(
                "Bewährtes BMWK-Förderprogramm für KMU mit Innovationsbezug, "
                "auch für Beratungs-/Software-Innovationen im Pharma-Umfeld."
            ),
            next_step=(
                "Innovationsbezug klar herausarbeiten; "
                "ggf. Kooperationsprojekt mit Forschungseinrichtung."
            ),
            region="DE",
            url="https://www.zim.de/",
        ),
        FundingMatch(
            name="go-digital (BMWK) — Beratung Digitalisierung",
            fit="Mittel",
            why=(
                "Zuschuss für Beratungs-/Digitalisierungsleistungen bei KMU-Kunden. "
                "Indirekt nutzbar: deine Pharma-Kunden können go-digital für "
                "deine Beratungsleistung einsetzen."
            ),
            next_step=(
                "Als autorisiertes Beratungsunternehmen registrieren — "
                "Voraussetzung: BAFA-Anerkennung."
            ),
            region="DE",
            url="https://www.bmwk.de/Redaktion/DE/Artikel/Digitale-Welt/foerderprogramm-go-digital.html",
        ),
    ],
    # Weitere Branchen ergänzbar
}


def find_funding_matches(p: BusinessPlanInput) -> list[FundingMatch]:
    """
    Liefert geeignete Fördermittel-Programme.

    Logik:
    1. Branchen-spezifische Programme (zuerst, wenn passend)
    2. Regionale Programme (wenn Region-Match)
    3. Föderale Programme (immer)
    """
    result: list[FundingMatch] = list(_FEDERAL_PROGRAMS)

    region = (p.region or "DE").upper()
    if region in _REGIONAL_PROGRAMS:
        result = _REGIONAL_PROGRAMS[region] + result

    industry = (p.industry or "generic").lower()
    if industry in _INDUSTRY_PROGRAMS:
        result = _INDUSTRY_PROGRAMS[industry] + result  # branchenspezifisch ganz oben

    return result
