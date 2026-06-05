# 📦 Update-Pack: Phase 5c — Branchen-Profile als 1. Klasse Bürger

**10 Dateien.** Keine neuen Dependencies. Kein DB-Schema-Bruch.

## Was das löst

**Vorher:** Die Pharma-Vorlage war im Businessplan-Generator versteckt.
Nicht-Pharma-User sahen sie trotzdem. Branche war nur Anzeige.

**Jetzt:** `User.branch` ist der zentrale Schalter der Plattform.
Wer ihn umstellt, sieht überall passende Inhalte:
- Chat-Plugin (Pharma-Mode)
- Businessplan-Vorlagen (gefiltert)
- (später) Agenten-Vorlagen

## Einbau

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/update-pack-5c/* .

# Cache leeren (sicherheitshalber)
find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} +

# Beide Server neu starten
# Terminal 1: Ctrl+C, dann ↑ Enter (uvicorn)
# Terminal 2: Ctrl+C, dann ↑ Enter (Streamlit)
```

## Tests

```bash
source .venv/bin/activate
pytest tests/ -q
# → 130 passed, 1 skipped
```

## Der Wow-Test in 4 Schritten

### Stufe 1 — Sidebar checken
1. Browser neu laden (Cmd+Shift+R)
2. Sidebar zeigt jetzt: **🏢 Mein Branchen-Profil [Dropdown]**

### Stufe 2 — Generic-User
1. Profil auf **"🌐 Generisch"** stellen
2. → 📊 Businessplan → Vorlage-Dropdown:
   - sieht: **KMU Standard**, **Verinaris (Beispiel)**
   - sieht NICHT: Pharma-Vorlage

### Stufe 3 — Pharma-User
1. Profil auf **"💊 Pharma-Beratung & Vertrieb"** stellen
2. Banner ändert sich zu *"Pharma-Mode aktiv"*
3. → 📊 Businessplan → Vorlage-Dropdown:
   - sieht: **Pharma-Beratung & Vertrieb**, **KMU Standard**, **Verinaris**
   - Pharma steht ganz oben

### Stufe 4 — Admin sieht alles
Wenn du als Admin eingeloggt bist, siehst du **alle** Vorlagen — egal welche
Branche eingestellt ist. Das ist gewollt: für Demos.

## Architektur-Änderung im Kurzüberblick

**Neue Stellen:**
- `app/branches/profiles.py` — zentrales Mapping-Modul (Branche → Industry/Templates)
- `app/api/profile.py` — `GET /profile/industries`, `GET /profile/me`, `PUT /profile/me/branch`

**Geänderte Stellen:**
- `app/api/businessplan.py` — Templates-Filter nach `User.branch`
- `app/main.py` — Profile-Router registriert
- `streamlit_app/app.py` — Sidebar mit Branchen-Wähler
- `streamlit_app/api_client.py` — Profile-API-Calls
- `app/models.py` — UserBranch-Docstring erweitert

## Vorbereitung für Phase 7 (Agenten)

Wenn wir später Agent-Vorlagen einführen, brauchen wir nur ein weiteres
Mapping in `profiles.py`:

```python
_BRANCH_TO_AGENTS["pharma"] = {
    "regulatorik_watcher_pharma",
    "sop_writer_pharma",
    ...
}
```

→ Branchen-Profil **trägt alle künftigen Module mit**.

## Kein Daten-Bruch

- Bestehende User behalten ihre `branch`-Einstellung
- Bestehende Businessplan-Daten bleiben unverändert
- `template_id` bleibt funktional (wird nicht ersetzt)

## Was als nächstes?

Vorschläge:
1. **Phase 7a** — Tool-Use-Fundament (für die 3 Kunden-Agenten)
2. **Admin-Dashboard** klassisch (Token-Charts, Audit-Log)
3. **Anwalts-Branche** als weiteres Profil (Demo-Vorbereitung)
4. **Erstmal spielen + Kunde antworten**
