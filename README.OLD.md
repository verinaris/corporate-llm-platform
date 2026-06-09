# Corporate LLM Platform

Eine **selbst gehostete LLM-Plattform** für Unternehmen — schrittweise aufgebaut zum Lernen.

## Vision

Ein "eigenes ChatGPT" für Firmen mit:
- Multi-User-Login mit Rollen
- Anbindung von Firmenwissen (RAG über PDFs/Docs)
- Austauschbare LLM-Provider (Claude, OpenAI, lokales Ollama)
- Token-/Kostenauswertung pro User und Modell

## Architektur (Analogie: Restaurant)

```
USER (Browser)
   |
   v
Streamlit-Frontend  (= Gastraum)        [Phase 2]
   |
   v
FastAPI Backend     (= Servicepersonal) [Phase 1 — bereits da]
 |   |       |        |
 v   v       v        v
SQLite ChromaDB  Claude  OpenAI/Ollama
(Kasse) (Rezept) (Koch1) (Koch2/3)
```

## Roadmap

| Phase | Inhalt | Status |
|-------|--------|--------|
| 0 | Setup, Repo-Struktur, Doku | ✅ |
| 1 | API-Gateway: FastAPI + Claude + Token-Logging | ✅ |
| 2 | Streamlit-Chat-Frontend + Multi-User + Rollen | ⬜ |
| 3 | RAG: PDF-Upload → ChromaDB → Antwort mit Firmenwissen | ⬜ |
| 4 | Multi-LLM-Routing: OpenAI + Ollama | ⬜ |
| 5 | Admin-Dashboard mit Token-/Kostenauswertung | ⬜ |

## Schnellstart (Phase 0 + 1)

### 1. Voraussetzungen

- Python ≥ 3.11
- Ein Anthropic-API-Key (https://console.anthropic.com/)

### 2. Installation

```bash
# Repo klonen (nachdem du es auf GitHub gepusht hast)
git clone https://github.com/DEIN-USER/corporate-llm-platform.git
cd corporate-llm-platform

# Virtual Environment anlegen
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# Dependencies installieren
pip install -r requirements.txt

# Environment-Datei vorbereiten
cp .env.example .env
# Jetzt .env öffnen und ANTHROPIC_API_KEY eintragen
```

### 3. Starten

```bash
uvicorn app.main:app --reload
```

Dann im Browser:
- **API-Doku (Swagger):** http://localhost:8000/docs
- **Health-Check:** http://localhost:8000/health
- **Stats:** http://localhost:8000/stats

### 4. Erstes Chat-Request senden

Über die Swagger-UI unter `/docs` → `POST /chat` → "Try it out":

```json
{
  "messages": [
    {"role": "user", "content": "Sag Hallo auf Deutsch."}
  ],
  "user_id": "test-user"
}
```

Oder per cURL:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hallo!"}],"user_id":"test"}'
```

### 5. Token-Auswertung ansehen

```bash
curl http://localhost:8000/stats
```

Du bekommst eine Aufstellung über:
- Gesamtzahl Requests
- Gesamttokens (input/output)
- Gesamtkosten in USD
- Aufschlüsselung pro Modell
- Aufschlüsselung pro User

## Projektstruktur

```
corporate-llm-platform/
├── app/
│   ├── api/              # HTTP-Endpoints (chat, health, stats)
│   ├── llm/              # LLM-Clients (anthropic, später openai, ollama)
│   ├── services/         # Token-Tracker
│   ├── config.py         # Settings aus .env
│   ├── database.py       # SQLite-Setup
│   ├── models.py         # DB-Tabellen
│   ├── schemas.py        # API-Request/Response-Formen
│   ├── pricing.py        # Modellpreise
│   └── main.py           # FastAPI-Einstieg
├── docs/                 # Phasen-Dokumentation
├── tests/                # Pytest-Tests
├── .env.example
├── .gitignore
└── requirements.txt
```

## Dokumentation

- [`docs/architecture.md`](docs/architecture.md) — Architektur-Überblick
- [`docs/phase-0-setup.md`](docs/phase-0-setup.md) — Phase 0: Setup
- [`docs/phase-1-gateway.md`](docs/phase-1-gateway.md) — Phase 1: API-Gateway

## Lizenz

Privates Lernprojekt — Lizenz nach Wahl ergänzen.
