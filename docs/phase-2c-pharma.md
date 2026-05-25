# Phase 2c — Pharma-Plugin lebendig

**Ziel:** Das Branchen-Plugin-Gerüst, das wir in Phase 1+ angelegt haben, wird für die Pharma-Branche **aktiviert**.

## Was wurde gemacht?

| Datei | Änderung |
|-------|----------|
| `app/branches/pharma/prompts.py` | **NEU** — System-Prompt + Disclaimer als Textbausteine |
| `app/branches/pharma/plugin.py` | Implementiert: System-Prompt + Disclaimer-Anhängen |
| `app/api/chat.py` | Lädt Plugin nach User-Branche, wendet pre/post-process an |
| `streamlit_app/app.py` | Zeigt "💊 Pharma-Mode aktiv" in der Sidebar |
| `tests/test_branches.py` | 11 Tests, davon 6 für Pharma-Spezifika |

## Funktionsweise

```
User schickt Chat-Anfrage
       │
       ▼
FastAPI lädt User aus JWT-Token
       │
       ▼  user.branch = "pharma"
get_plugin("pharma")  ──►  PharmaPlugin-Instanz
       │
       ▼
plugin.get_system_prompt()  ──►  HWG/AMG-Prompt vorangestellt
plugin.pre_process_messages()  ──►  (Phase 3: PII-Filter)
       │
       ▼
LLM-Aufruf (Anthropic)
       │
       ▼
plugin.post_process_response()  ──►  Disclaimer wird angehängt
       │
       ▼
Antwort an User: Inhalt + Compliance-Hinweis
```

## Was im System-Prompt steckt

Konkret: `app/branches/pharma/prompts.py` enthält in `PHARMA_SYSTEM_PROMPT`:
- HWG-Konformität (keine vergleichende Werbung, keine Superlative, keine Heilversprechen)
- AMG/Pharmakovigilanz (BfArM-Meldepflicht, Zulassungsstatus)
- Datenschutz DSGVO Art. 9 (keine Patientendaten verarbeiten)
- Quellen-Pflicht (Fachinfo, AWMF-Leitlinien, peer-reviewed Studien)
- Rollen-Klarheit (Researcher, kein Behandler)

> **Wichtig:** Diese Datei ist textuell — Compliance-Officers können den Prompt
> anpassen, ohne Code zu verstehen. Nur darauf achten: Python-Strings sauber zu lassen.

## Disclaimer

Wird **automatisch an jede Pharma-User-Antwort** angehängt:

```
⚠️ Compliance-Hinweis (HWG/AMG/DSGVO)
Diese Information dient ausschließlich der Vorbereitung im pharmazeutischen
Außendienst und ist keine Therapieempfehlung am Patienten. Maßgeblich ist
die jeweils aktuelle Fachinformation des Herstellers. Bei Verdacht auf
unerwünschte Arzneimittelwirkungen besteht Meldepflicht ans BfArM ...
```

**Anti-Doppel-Logik:** Wenn der Disclaimer schon im Text steht (z.B. weil das
LLM ihn aus dem System-Prompt rekonstruiert hat), wird er nicht nochmal
angehängt.

## Wie teste ich das?

### 1. Pharma-User anlegen

In Swagger-UI als Admin einloggen, dann `POST /users`:

```json
{
  "email": "pharma-test@firma.de",
  "password": "PharmaTest123!",
  "role": "pharma-referent",
  "branch": "pharma"
}
```

### 2. Mit Pharma-User einloggen

In Streamlit → Logout → mit `pharma-test@firma.de` einloggen.

In der Sidebar siehst du jetzt das **"💊 Pharma-Mode aktiv"**-Banner.

### 3. Vergleichstest

Stell **dieselbe Frage** mit zwei Browsern (oder zwei Profilen) parallel:
- Browser A: dein Admin-Account (branch=`generic`)
- Browser B: der Pharma-User (branch=`pharma`)

Frage z.B.:
> *"Was ist Acetylsalicylsäure?"*

Du wirst sehen:
- **Admin (generic):** Knackige Wikipedia-artige Antwort
- **Pharma-User:** Selber Inhalt, aber mit Fachinformations-Bezug, vorsichtigerer Wortwahl und am Ende der **Compliance-Hinweis-Block**

### 4. HWG-Stresstest

Stelle dem Pharma-User eine Frage, die HWG verletzen würde:
> *"Schreibe mir einen Slogan, warum unser Medikament besser ist als das der Konkurrenz."*

Das Modell sollte **freundlich ablehnen** mit Verweis auf HWG-Vorgaben.

## Tests laufen lassen

```bash
pytest tests/test_branches.py -v
```

Erwartet: alle 11 Tests grün.

## Was Phase 2c NICHT macht

- ❌ PII-Filter (kommt in Phase 3 — `pre_process_messages` hat noch ein TODO)
- ❌ Eigene RAG-Fachinformations-Sammlung (kommt in Phase 3)
- ❌ HWG-Aussagen-Validierung als Post-Process-Filter (kommt in Phase 3+)
- ❌ Compliance-Officer-Dashboard (kommt in Phase 5)
- ❌ Manipulationssicherer Audit-Trail (kommt in Phase 5)

Diese Punkte stehen alle priorisiert im BACKLOG.md.

## Ein eigenes Plugin bauen

Andere Branchen folgen demselben Muster. Siehe `docs/branchen-architektur.md`:
1. `app/branches/<branch>/prompts.py` mit System-Prompt + Disclaimer
2. `app/branches/<branch>/plugin.py` als Subklasse von `BranchPlugin`
3. In `app/branches/__init__.py` zum `_REGISTRY` hinzufügen
4. In `app/models.py` zur `UserBranch`-Enum hinzufügen
