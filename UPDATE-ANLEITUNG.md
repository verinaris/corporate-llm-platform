# 📦 Update-Pack: Phase 2b — Streamlit-Frontend

**Was ist drin:** 10 Dateien — komplettes Streamlit-Frontend + erweiterte `requirements.txt`. **Keine Backend-Änderungen.**

---

## Einbau in 5 Schritten

### 1. Backend-Server kann weiterlaufen
Nicht nötig zu stoppen — wir ändern nichts am Backend.

### 2. Update-Pack ins Projekt kopieren

Im Finder oder Terminal — der `streamlit_app/`-Ordner und die zwei einzelnen Dateien (`requirements.txt`, `docs/phase-2b-frontend.md`) ins Projekt:

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/update-pack-2b/* .
```

### 3. Streamlit installieren

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Neu kommt rein: `streamlit==1.40.0` (dauert ~1-2 Minuten, lädt Dependencies wie altair, pandas, pyarrow).

### 4. Frontend starten — in einem NEUEN Terminal

**Wichtig:** Backend und Frontend brauchen je ein eigenes Terminal!

**Terminal 1** (das du schon hast): Backend läuft
```bash
uvicorn app.main:app --reload
```

**Terminal 2** (neu öffnen in VS Code: `Terminal` → `New Terminal`):
```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
source .venv/bin/activate
streamlit run streamlit_app/app.py
```

Streamlit öffnet automatisch deinen Browser auf `http://localhost:8501`.

### 5. Einloggen + ausprobieren

- E-Mail: `sascha.kern@nobelimpressions.com`
- Passwort: dein Bootstrap-Passwort aus `.env`

→ Du landest direkt im Chat-UI. 🎉

---

## Was du jetzt kannst

| Feature | Wo |
|---------|-----|
| **Chat mit Verlauf** | Hauptbereich — wie ChatGPT |
| **Modell wechseln** | Sidebar links → Dropdown |
| **Token/Kosten pro Antwort** | Unter jeder Claude-Antwort als Caption |
| **Gesamt-Verbrauch ansehen** | Sidebar → "📊 Verbrauch" |
| **Verlauf löschen** | Sidebar → "🗑️ Verlauf löschen" |
| **Logout** | Sidebar → "🚪 Logout" |

---

## Troubleshooting

**"Backend nicht erreichbar"** → Terminal 1 (uvicorn) ist nicht aktiv. Erst Backend starten, dann Streamlit.

**"Address already in use" bei Streamlit** → Schon ein Streamlit-Prozess läuft.
```bash
pkill -f streamlit
```
Dann Streamlit erneut starten.

**Modul-Fehler beim Streamlit-Start** → Du startest aus einem falschen Verzeichnis. Streamlit MUSS aus dem Projekt-Root gestartet werden:
```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform   # WICHTIG!
streamlit run streamlit_app/app.py
```

**Browser öffnet nicht automatisch** → Manuell auf http://localhost:8501 gehen.

---

## Git-Commit

```bash
git add streamlit_app/ requirements.txt docs/phase-2b-frontend.md
git commit -m "Phase 2b: Streamlit-Frontend (Login, Chat, Stats)"
git push
```

(Oder über VS Code Source Control wie gewohnt.)

---

## Lesestoff

- `docs/phase-2b-frontend.md` — Konzept, Architektur, Features-Übersicht
