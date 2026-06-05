"""
Branchen-spezifische Härtungs-Checks.

Ergänzt die generischen Checks aus `checks.py` um branchen-spezifische
Prüfungen. Dispatcher nach `BusinessPlanInput.industry`.

**Designprinzip:** Compliance-Tiefe "Mittel" — wir prüfen Bewusstsein und
Begrifflichkeit, nicht paragrafen-genaue Korrektheit. Letzteres gehört
in den Anwalts-Termin.
"""

import re

from app.services.businessplan.models import (
    BusinessPlanInput,
    CheckResult,
    FinancialYear,
)


# ============================================================ #
# Pharma-spezifische Checks (HWG/AMG/FSA/DSGVO Art. 9)
# ============================================================ #

# Begriffe, die HWG-relevant sein können (Werbeaussagen-Filter)
_HWG_SUPERLATIVE_PATTERNS = [
    r"\b(beste|besten|bester|stärkste|stärksten|größte|größten)\b",
    r"\b(einzig|einzige|einzigartig|einmalig|konkurrenzlos)\b",
    r"\b(garantiert|100\s*%|hundertprozentig)\b",
    r"\b(heilt|heilung|wundermittel)\b",
    r"\b(nebenwirkungsfrei|risikolos)\b",
]


def _contains_hwg_critical_language(text: str) -> list[str]:
    """Sucht in einem Text nach HWG-kritischen Formulierungen."""
    if not text:
        return []
    findings = []
    text_lower = text.lower()
    for pattern in _HWG_SUPERLATIVE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            findings.append(match.group(0))
    return findings


def _check_pharma(
    p: BusinessPlanInput,
    financials: list[FinancialYear],
) -> list[CheckResult]:
    """Pharma-Beratung & Vertrieb: 4 zusätzliche Bewusstseins-Checks."""
    checks: list[CheckResult] = []

    # 1. HWG-Werbeaussagen-Filter (USP + Lösungsbeschreibung scannen)
    full_text = f"{p.usp} {p.solution} {p.mission}".strip()
    hwg_hits = _contains_hwg_critical_language(full_text)
    if hwg_hits:
        checks.append(
            CheckResult(
                area="Pharma · HWG",
                status="Nachschärfen",
                finding=(
                    f"Werbe-/Lösungstexte enthalten möglicherweise HWG-kritische "
                    f"Formulierungen: {', '.join(set(hwg_hits))}."
                ),
                recommendation=(
                    "Superlative, Heilungs-/Garantie-Aussagen entfernen. "
                    "HWG verbietet u.a. irreführende Werbung und unzulässige "
                    "Wirkversprechen (§§ 3, 11 HWG). Im Zweifel: anwaltlicher "
                    "Werbeaussagen-Check vor Veröffentlichung."
                ),
            )
        )
    else:
        checks.append(
            CheckResult(
                area="Pharma · HWG",
                status="OK",
                finding=(
                    "Keine offensichtlichen HWG-kritischen Formulierungen "
                    "in den Plan-Texten erkannt."
                ),
                recommendation=(
                    "Vor Markteinführung: jede Werbeaussage einzeln gegen "
                    "HWG, AMG (Zulassungsbezug) und FSA-Kodex prüfen lassen. "
                    "Stichproben-Audit ein Mal pro Jahr empfohlen."
                ),
            )
        )

    # 2. DSGVO Art. 9 — Gesundheitsdaten (immer für Pharma, kontextabhängig)
    target_lower = (p.target_customers or "").lower()
    has_health_data_context = any(
        keyword in target_lower
        for keyword in [
            "patient", "praxis", "klinik", "krankenhaus", "arzt", "ärzt",
            "apothek", "hcp", "behandl",
        ]
    )
    has_art9_mention = "art. 9" in (p.compliance_status or "").lower() or \
                      "art 9" in (p.compliance_status or "").lower() or \
                      "gesundheitsdaten" in (p.compliance_status or "").lower()

    if has_health_data_context and has_art9_mention:
        checks.append(
            CheckResult(
                area="Pharma · DSGVO Art. 9",
                status="OK",
                finding=(
                    "Zielgruppe lässt auf Verarbeitung besonderer Kategorien "
                    "(Gesundheitsdaten) schließen; Art. 9 DSGVO ist im "
                    "Compliance-Status berücksichtigt."
                ),
                recommendation=(
                    "Für patienten-/praxisnahe Verarbeitung: "
                    "Datenschutz-Folgenabschätzung (DSFA), explizite "
                    "Einwilligungen oder gesetzliche Erlaubnisgrundlage, "
                    "AVV mit allen Auftragsverarbeitern, technisch-"
                    "organisatorische Maßnahmen (TOMs) dokumentieren."
                ),
            )
        )
    elif has_health_data_context and not has_art9_mention:
        checks.append(
            CheckResult(
                area="Pharma · DSGVO Art. 9",
                status="Kritisch",
                finding=(
                    "Zielgruppe deutet auf Gesundheitsdaten hin, aber "
                    "Art. 9 DSGVO wird im Compliance-Status nicht erwähnt."
                ),
                recommendation=(
                    "Vor Bank-/Förder-Gespräch: Verarbeitungsstrategie "
                    "für besondere Kategorien personenbezogener Daten "
                    "(Art. 9 DSGVO) explizit dokumentieren — "
                    "Erlaubnisgrundlage, DSFA-Pflicht, AVV, "
                    "TOMs, Löschkonzept."
                ),
            )
        )
    else:
        # Kein direkter Gesundheitsdaten-Bezug erkannt — trotzdem hinweisen
        checks.append(
            CheckResult(
                area="Pharma · DSGVO Art. 9",
                status="Nachschärfen",
                finding=(
                    "Aktuelle Zielgruppe deutet nicht direkt auf "
                    "Gesundheitsdaten hin — Pharma-Mandate können sich "
                    "aber jederzeit dorthin entwickeln."
                ),
                recommendation=(
                    "Vorab klären: Welche Mandate dürfen Art.-9-Daten berühren "
                    "(z.B. Außendienst-Berichte mit Praxis-Bezug)? "
                    "Standard-Verfahren für DSFA, AVV, TOMs und "
                    "Erlaubnisgrundlage in der Beratungs-Methodik verankern."
                ),
            )
        )

    # 3. Pharmakovigilanz-Bewusstsein
    pv_mentioned = (
        "pharmakovigilanz" in (p.compliance_status or "").lower()
        or "meldepflicht" in (p.compliance_status or "").lower()
        or "pharmakovigilanz" in (p.solution or "").lower()
    )
    if pv_mentioned:
        checks.append(
            CheckResult(
                area="Pharma · Pharmakovigilanz",
                status="OK",
                finding="Pharmakovigilanz-Bezug ist im Plan adressiert.",
                recommendation=(
                    "Meldepfade für Nebenwirkungs-/Beobachtungs-Meldungen "
                    "an BfArM/PEI im Beratungs-Workflow vorhalten. "
                    "10-Jahres-Aufbewahrung in IT-Strategie verankern."
                ),
            )
        )
    else:
        checks.append(
            CheckResult(
                area="Pharma · Pharmakovigilanz",
                status="Nachschärfen",
                finding=(
                    "Pharmakovigilanz / Meldepflichten werden im Plan nicht erwähnt."
                ),
                recommendation=(
                    "Für jeden Beratungs-/Vertriebs-Use-Case prüfen, ob "
                    "Pharmakovigilanz-Bezüge entstehen können (z.B. "
                    "Patienten-Feedback in Außendienst-Berichten). "
                    "Meldepfade und 10-Jahres-Retention dokumentieren."
                ),
            )
        )

    # 4. KI-Datenverarbeitung — lokales LLM empfohlen
    compliance_text = (p.compliance_status or "").lower()
    risks_text = (p.risks or "").lower()
    has_local_llm_strategy = (
        "lokal" in compliance_text
        or "ollama" in compliance_text
        or "on-premise" in compliance_text
        or "on premise" in compliance_text
        or "selbst gehostet" in compliance_text
        or "self-hosted" in compliance_text
    )

    if has_health_data_context and not has_local_llm_strategy:
        checks.append(
            CheckResult(
                area="Pharma · KI-Hosting",
                status="Nachschärfen",
                finding=(
                    "Patienten-/praxisnahe Daten geplant, aber keine explizite "
                    "Strategie für lokales/EU-souveränes KI-Hosting genannt."
                ),
                recommendation=(
                    "Empfehlung: Für Verarbeitung mit Art.-9-Bezug auf "
                    "lokal hostbare Modelle (z.B. Ollama-Stack) setzen — "
                    "Daten verlassen das Haus nicht. Cloud-LLMs nur für "
                    "ent-personalisierte Standard-Aufgaben. EU AI Act "
                    "Risikoklassifizierung pro Use-Case dokumentieren."
                ),
            )
        )

    return checks


# ============================================================ #
# Dispatcher
# ============================================================ #

def run_industry_checks(
    p: BusinessPlanInput,
    financials: list[FinancialYear],
) -> list[CheckResult]:
    """
    Führt branchen-spezifische Checks aus.

    Dispatch nach `p.industry`. Generische Branche → keine zusätzlichen Checks.
    """
    industry = (p.industry or "generic").lower()

    if industry == "pharma_beratung_vertrieb":
        return _check_pharma(p, financials)

    # Weitere Branchen kommen hier rein (legal, tax, energy, ...)
    return []
