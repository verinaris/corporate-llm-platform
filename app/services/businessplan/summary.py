"""
LLM-gestützte Executive Summary.

**Kernunterschied zum Verinaris-MVP:** Nutzt unsere bestehende
Provider-Abstraktion (Anthropic + Ollama) statt direktem `requests.post()`.

Vorteile:
- Cloud (Claude) ODER lokal (Ollama) — User entscheidet
- Token-Tracking funktioniert automatisch (via token_tracker)
- Konsistente Fehlerbehandlung mit dem Rest der Plattform

Wenn kein LLM verfügbar oder gewünscht: regelbasierter Fallback-Text.
"""

import json

from app.llm.anthropic_client import AnthropicClient
from app.llm.base import BaseLLMClient
from app.llm.ollama_client import OllamaClient
from app.schemas import ChatMessage
from app.services.businessplan.models import (
    BusinessPlanInput,
    CheckResult,
)


def _build_prompt(p: BusinessPlanInput, checks: list[CheckResult]) -> str:
    """Baut den Prompt für die Executive Summary."""
    checks_text = json.dumps(
        [{"area": c.area, "status": c.status, "finding": c.finding} for c in checks],
        ensure_ascii=False,
    )
    return f"""Erstelle eine präzise, bankentaugliche Executive Summary auf Deutsch.

Unternehmen: {p.startup_name}
Rechtsform: {p.legal_form}
Standort: {p.location}
Mission: {p.mission}

Problem: {p.problem}
Lösung: {p.solution}
Zielkunden: {p.target_customers}
USP: {p.usp}
Umsatzmodell: {p.revenue_model}

Aktuelle Prüfbefunde aus Härtungs-Checks:
{checks_text}

WICHTIG:
- Maximal 180 Wörter
- Sachlicher MBA-Stil, keine Marketing-Phrasen
- Schwächen ehrlich benennen, mit konkretem Handlungsbedarf
- Keine erfundenen Zahlen — wenn etwas fehlt, das auch sagen
- KEIN Disclaimer und KEINE Begrüßung — nur die Summary"""


def _fallback_summary(p: BusinessPlanInput, checks: list[CheckResult]) -> str:
    """Regelbasierter Fallback wenn kein LLM verfügbar."""
    critical_count = sum(1 for c in checks if c.status == "Kritisch")
    nachscharfen_count = sum(1 for c in checks if c.status == "Nachschärfen")

    base = (
        f"{p.startup_name or 'Das Unternehmen'} positioniert sich mit einem "
        f"Lösungsangebot im Bereich '{(p.solution or 'KMU')[:80]}'. "
    )
    if p.usp:
        base += f"Differenzierungsmerkmal: {p.usp[:200]}. "

    if critical_count > 0:
        base += (
            f"Der Plan zeigt aktuell {critical_count} kritische Schwachstelle"
            f"{'n' if critical_count != 1 else ''}, die vor "
            f"einem Bank- oder Förder-Gespräch zu beheben sind. "
        )
    elif nachscharfen_count > 0:
        base += (
            f"Der Plan ist im Kern tragfähig, weist aber "
            f"{nachscharfen_count} Bereich"
            f"{'e' if nachscharfen_count != 1 else ''} auf, in denen nachgeschärft "
            f"werden sollte. "
        )
    else:
        base += "Der Plan wirkt in den geprüften Dimensionen tragfähig. "

    base += (
        "Empfohlene nächste Schritte: belastbare Pilotkunden, "
        "monatliche Liquiditätsplanung für 24 Monate und vollständige "
        "Compliance-Dokumentation (TOMs, AVV, Löschkonzept, EU-AI-Act-"
        "Risikoklassifizierung)."
    )

    return base


async def generate_executive_summary(
    p: BusinessPlanInput,
    checks: list[CheckResult],
    model: str | None = None,
    max_tokens: int = 400,
) -> tuple[str, str]:
    """
    Erzeugt eine Executive Summary.

    Args:
        p: Eingaben
        checks: Vorab berechnete Härtungs-Checks
        model: Modell-ID (z.B. 'claude-sonnet-4-6' oder 'qwen2.5:7b').
               None = Fallback (regelbasiert).
        max_tokens: Token-Limit für die Generierung

    Returns:
        (summary_text, llm_used) — wobei llm_used z.B. 'claude-sonnet-4-6'
        oder 'rule-based' (Fallback)
    """
    if not model:
        return _fallback_summary(p, checks), "rule-based"

    # Provider auswählen — analog zu app/api/chat.py
    client: BaseLLMClient
    if model.startswith("claude-"):
        client = AnthropicClient()
    elif ":" in model or model.lower().startswith((
        "llama", "qwen", "mistral", "phi", "gemma", "codellama",
        "deepseek",
    )):
        client = OllamaClient()
    else:
        # Unbekanntes Modell — Fallback
        return _fallback_summary(p, checks), "rule-based"

    prompt = _build_prompt(p, checks)

    try:
        result = await client.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model,
            max_tokens=max_tokens,
        )
        return result.content.strip(), model
    except Exception as exc:
        # Fallback, aber im llm_used vermerken dass es nicht ging
        fallback = _fallback_summary(p, checks)
        return (
            f"{fallback}\n\n"
            f"_(LLM-Erzeugung war nicht möglich: {type(exc).__name__})_"
        ), "rule-based-after-error"
