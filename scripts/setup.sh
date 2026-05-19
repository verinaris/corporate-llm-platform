#!/usr/bin/env bash
# Setup-Skript für Corporate LLM Platform
# Führt die einmaligen Setup-Schritte automatisiert aus.

set -e  # bei Fehler abbrechen

echo "🚀 Corporate LLM Platform Setup"
echo "==============================="

# Python-Version prüfen
PY_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
echo "✓ Python ${PY_VERSION} gefunden"

# Virtual Environment anlegen
if [ ! -d ".venv" ]; then
    echo "→ Lege .venv an..."
    python3 -m venv .venv
else
    echo "✓ .venv existiert bereits"
fi

# Aktivieren + Dependencies
echo "→ Aktiviere .venv und installiere Dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✓ Dependencies installiert"

# .env vorbereiten
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env aus .env.example kopiert"
    echo ""
    echo "⚠️  Bitte ANTHROPIC_API_KEY in .env eintragen!"
else
    echo "✓ .env existiert bereits"
fi

# data/-Ordner
mkdir -p data
echo "✓ data/-Verzeichnis angelegt"

echo ""
echo "Setup abgeschlossen. Starten mit:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload"
