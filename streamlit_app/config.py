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
