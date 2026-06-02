"""
Streamlit-App-Konfiguration.

Backend-URL kann über ENV überschrieben werden:
    export BACKEND_URL=http://localhost:8000
"""

import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# UI-Strings
APP_TITLE = "Corporate LLM Platform"
APP_ICON = "🤖"

# Verfügbare Modelle (Anzeige-Label → Modell-ID)
AVAILABLE_MODELS: dict[str, str] = {
    "Haiku 4.5  ·  schnell & günstig":  "claude-haiku-4-5",
    "Sonnet 4.6  ·  ausgewogen (Default)": "claude-sonnet-4-6",
    "Opus 4.7  ·  stärkstes Modell":    "claude-opus-4-7",
}

DEFAULT_MODEL_LABEL = "Sonnet 4.6  ·  ausgewogen (Default)"

# ----------------------------------------------------------------------- #
# Währungs-Anzeige
# ----------------------------------------------------------------------- #
# Die Anthropic-API rechnet in USD. Wir zeigen lokal in EUR.
# Wechselkurs ist eine Schätzung (Mid-Market), kann über ENV überschrieben
# werden. Für eine echte Rechnungs-Genauigkeit später: tägliches Fetch
# von EZB-Referenzkurs.
USD_TO_EUR = float(os.getenv("USD_TO_EUR", "0.92"))


def usd_to_eur(usd: float) -> float:
    """Konvertiert USD-Beträge in EUR (Annäherung)."""
    return usd * USD_TO_EUR


def format_eur(usd: float, decimals: int = 4) -> str:
    """
    Formatiert einen USD-Betrag als EUR-String mit deutschem Format.

    Beispiel: 0.3214 USD → '0,2957 €'
    """
    eur = usd_to_eur(usd)
    s = f"{eur:.{decimals}f}"
    # Deutsche Notation: Punkt → Komma
    s = s.replace(".", ",")
    return f"{s} €"

