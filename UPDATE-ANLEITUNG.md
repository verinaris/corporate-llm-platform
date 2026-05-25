# 📦 Update-Pack: Quick Wins (BFSG + Cloud-Readiness)

**Was ist drin:** 8 Dateien — 3 geänderte + 5 neue. **Keine Datenbank-Änderungen, kein .env-Eingriff nötig.**

## Was geändert wird

### Geändert (überschrieben):
- `app/config.py` — Production-Validation, Anthropic-Region-Option, CORS-Vorbereitung
- `app/llm/anthropic_client.py` — nutzt jetzt optional EU-Region
- `streamlit_app/app.py` — Sprache `de`, Focus-Ring, About-Menü

### Neu:
- `.streamlit/config.toml` — Theme, Telemetrie aus
- `Dockerfile` — Backend-Container (für später)
- `.dockerignore`
- `docker-compose.yml` — lokales Test-Setup
- `docs/quick-wins-bfsg-cloud.md`

---

## Einbau in 3 Schritten

### 1. Beide Server stoppen (Backend + Streamlit)
In Terminal 1 und Terminal 2 jeweils: **`Ctrl + C`**

### 2. Update-Pack ins Projekt kopieren

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/update-pack-quickwins/* .
```

### 3. Beide Server neu starten

**Terminal 1:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2:**
```bash
streamlit run streamlit_app/app.py
```

→ Im Browser auf `http://localhost:8501` Hard-Reload (`Cmd+Shift+R`).

Du solltest sehen:
- Sauberere Streamlit-Optik (Standard-Theme bleibt, aber Telemetrie ist aus)
- Im Hauptbereich/Sidebar: bessere Tab-/Fokus-Markierung beim Drüberklicken

---

## Was die Production-Validation tut

Wenn du irgendwann in der `.env` `APP_ENV=production` setzt, prüft Pydantic beim Start:
- JWT_SECRET muss stark sein (≥ 32 Zeichen, nicht Default)
- APP_DEBUG=false (kein Stacktrace-Leak)

Wenn was nicht passt, **startet die App nicht**, sondern zeigt eine klare Fehlermeldung. So kannst du nicht versehentlich mit unsicherer Config produktiv gehen.

→ **Für jetzt bleibt `APP_ENV=development`** — keine Auswirkung im Alltag.

---

## Git-Commit

```bash
git add .
git commit -m "Quick Wins: BFSG (Accessibility) + Cloud-Readiness Vorbereitung"
git push
```

---

## Lesestoff

- `docs/quick-wins-bfsg-cloud.md` — was wir tun, was später kommt, welche EU-Provider relevant sind

## Was kommt im BACKLOG

Ich schicke dir gleich noch eine **erweiterte BACKLOG.md** mit zwei neuen Sektionen:
- 🌐 Accessibility (BFSG/EAA/WCAG)
- ☁️ Cloud-Readiness & Deployment

So weißt du genau, was später noch ansteht.
