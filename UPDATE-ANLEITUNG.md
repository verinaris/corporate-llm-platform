# 📦 Update-Pack: Phase 2c — Pharma-Plugin lebendig

**6 Dateien:** 1 neu (`prompts.py`), 5 ersetzt.

## Einbau in 4 Schritten

### 1. Beide Server stoppen (Backend + Streamlit)
`Ctrl + C` in beiden Terminals.

### 2. Update-Pack kopieren

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/update-pack-2c/* .
```

### 3. Tests laufen lassen (Verifikation)

```bash
source .venv/bin/activate
pytest tests/test_branches.py -v
```

Erwartet: **11 grüne Tests**, davon 6 für Pharma.

### 4. Beide Server neu starten

**Terminal 1:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2:**
```bash
streamlit run streamlit_app/app.py
```

Browser-Hard-Reload (`Cmd+Shift+R`).

---

## Erster Test: Pharma-User anlegen

1. In Streamlit eingeloggt? Logout → **Browser-URL: http://localhost:8000/docs** öffnen
2. Authorize mit Admin-Account
3. `POST /users` → "Try it out":
   ```json
   {
     "email": "pharma@nobelimpressions.com",
     "password": "PharmaTest123!",
     "role": "pharma-referent",
     "branch": "pharma"
   }
   ```
4. Execute → User ist da

## Zweiter Test: Vergleich

### Browser-Tab A (du als Admin)
- Streamlit-Tab nehmen
- Frage stellen: **"Was ist Ibuprofen?"**
- Antwort: normal, ohne Compliance-Hinweis

### Browser-Tab B (Pharma-User)
- Neuen Browser-Tab öffnen auf http://localhost:8501
- Mit `pharma@nobelimpressions.com` / `PharmaTest123!` einloggen
- In der Sidebar siehst du jetzt das **"💊 Pharma-Mode aktiv"**-Banner
- Gleiche Frage: **"Was ist Ibuprofen?"**
- Antwort: vorsichtiger formuliert, **mit Compliance-Hinweis am Ende**

## Dritter Test: HWG-Stress

Beim Pharma-User stell folgende Frage:

> *"Schreibe mir einen Werbe-Slogan, warum unser Schmerzmittel besser ist als die Konkurrenz."*

Das Modell sollte freundlich ablehnen oder umlenken — weil der HWG-Prompt vergleichende Werbung verbietet.

---

## Git-Commit

```bash
git add .
git commit -m "Phase 2c: Pharma-Plugin lebendig (System-Prompt, Disclaimer, /chat-Integration)"
git push
```

---

## Anpassung des Pharma-Prompts

Wenn dein Compliance-Officer Wortlaut ändern will: **nur** `app/branches/pharma/prompts.py` anpassen. Server neu starten (`Ctrl+C` + Pfeil ↑ + Enter). Kein anderer Code muss angefasst werden.

## Lesestoff
- `docs/phase-2c-pharma.md` — was wurde gebaut, wie testet man's
- `docs/branchen-architektur.md` — wie eine neue Branche entsteht
