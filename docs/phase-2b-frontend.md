# Phase 2b — Streamlit-Frontend

**Ziel:** Browser-Frontend mit Login, Chat-UI, Modell-Wahl und Stats-Ansicht.

## Was wurde gebaut?

```
streamlit_app/                  ← komplett NEU
├── __init__.py
├── app.py                      Haupt-Einstieg + Auth-Routing + Sidebar
├── api_client.py               Backend-Kommunikation (httpx)
├── config.py                   Streamlit-Einstellungen
└── pages/
    ├── __init__.py
    ├── login_page.py
    ├── chat_page.py
    └── stats_page.py
```

**Keine Backend-Änderungen** — Streamlit spricht nur die existierende API an.

## Architektur

```
Browser
   │
   ▼  Port 8501
Streamlit (streamlit_app/)
   │
   ▼  Port 8000 (HTTP, intern)
FastAPI Backend (app/)
   │
   ▼
SQLite + Anthropic API
```

**Wichtig:** Beide Prozesse müssen laufen!

## Starten

### Terminal 1 — Backend
```bash
cd /Pfad/zum/projekt
source .venv/bin/activate
uvicorn app.main:app --reload
```
→ Backend auf http://localhost:8000

### Terminal 2 — Frontend
```bash
cd /Pfad/zum/projekt
source .venv/bin/activate
streamlit run streamlit_app/app.py
```
→ Streamlit auf http://localhost:8501 (öffnet sich automatisch im Browser)

## Features

### Login-Seite
- E-Mail + Passwort
- Speichert JWT-Token in `st.session_state`
- Bei falschem Login: klare Fehlermeldung
- Bei Backend-Ausfall: hilfreiche Meldung

### Chat-UI
- Echtes Chat-Layout (wie ChatGPT)
- Konversations-Verlauf wird mitgeschickt (Multi-Turn)
- Modell-Wahl in der Sidebar
- Nach jeder Antwort: Token-Verbrauch + Kosten + Latenz unter der Nachricht
- "Verlauf löschen"-Button in der Sidebar

### Stats-Seite
- Top-Kacheln: Requests, Tokens, Kosten
- Aufschlüsselung pro Modell (Tabelle)
- Aufschlüsselung pro User (für Admin: alle, sonst: eigene)
- "Aktualisieren"-Button

### Sidebar
- User-Info (E-Mail, Rolle, Branche)
- Navigation
- Modell-Auswahl
- Verlauf löschen
- Logout

## Token-Handling

**Wo wird der Token gespeichert?** In `st.session_state["token"]` — lebt nur in der aktuellen Browser-Session.

**Was passiert beim Neuladen?** Token ist weg, neu einloggen nötig. (Für eine echte Cookie-Persistenz später: `st.context.cookies` oder externe Library.)

**Token-Ablauf?** 24h (`JWT_EXPIRE_HOURS` in `.env`). Wenn der Token abgelaufen ist, validiert die App ihn beim nächsten Seitenwechsel und schickt automatisch zurück zum Login.

## Modell-Wahl

In `streamlit_app/config.py` definiert:
```python
AVAILABLE_MODELS = {
    "Haiku 4.5  ·  schnell & günstig":  "claude-haiku-4-5",
    "Sonnet 4.6  ·  ausgewogen (Default)": "claude-sonnet-4-6",
    "Opus 4.7  ·  stärkstes Modell":    "claude-opus-4-7",
}
```

Möchtest du Modelle hinzufügen/entfernen: einfach dieses Dict anpassen.

## Backend-URL ändern

Standardmäßig `http://localhost:8000`. Für andere URLs (z.B. wenn Backend auf Server läuft):

```bash
export BACKEND_URL=https://api.deinefirma.de
streamlit run streamlit_app/app.py
```

## Was Phase 2b NICHT bringt

- ❌ Persistente Konversationen über Browser-Neustart (Phase 2c+)
- ❌ Mehrere parallele Chats / Sidebar-Listen wie ChatGPT (Phase 3)
- ❌ Datei-Upload (Phase 3, RAG)
- ❌ Admin-UI für User-Verwaltung (siehe Notiz unten)
- ❌ Pharma-Plugin sichtbar (kommt in 2c)

> **Admin-User-Verwaltung:** Aktuell nur über Swagger-UI (`http://localhost:8000/docs`, `/users`-Endpoints). Frontend-Admin-Bereich folgt in einer späteren Phase.

## Troubleshooting

**"Backend nicht erreichbar"** → Terminal 1 (uvicorn) läuft nicht. Erst Backend starten.

**Login funktioniert nicht** → Bootstrap-Admin korrekt in `.env`? `python scripts/debug_login.py` (wenn vorhanden) oder Diagnose-Snippet aus Phase 2a.

**"Address already in use" beim Streamlit-Start** → Schon ein Streamlit auf 8501. Mit `pkill -f streamlit` killen oder anderen Port wählen: `streamlit run streamlit_app/app.py --server.port 8502`.

**Modul nicht gefunden** → Streamlit muss aus dem Projekt-Root gestartet werden, damit `from streamlit_app.xxx` funktioniert.
