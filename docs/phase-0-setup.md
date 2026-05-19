# Phase 0 — Setup

**Ziel:** Projekt aufsetzen, Konventionen festlegen, Umgebung lauffähig machen.

## Was wurde gemacht?

### 1. Verzeichnisstruktur
```
corporate-llm-platform/
├── app/         # Anwendungs-Code
├── docs/        # Diese Dokumentation
├── tests/       # Pytest-Tests
└── scripts/     # Helper-Skripte
```

### 2. Dependency-Management
**`requirements.txt`** listet alle Python-Pakete mit festen Versionen.

> Warum feste Versionen? Damit das Projekt in 6 Monaten noch genauso läuft wie heute. Eine neuere FastAPI-Version könnte Breaking Changes haben.

### 3. Konfiguration über `.env`
- `.env.example` ist eingecheckt → zeigt, welche Variablen es gibt
- `.env` ist in `.gitignore` → echte Keys landen NIE im Git

**Analogie:** `.env.example` ist die leere Spalte einer Excel-Tabelle, `.env` ist deine ausgefüllte private Kopie.

### 4. .gitignore
Verhindert, dass Müll oder Geheimnisse versehentlich in Git landen:
- `.env` (API-Keys!)
- `.venv/` (virtuelle Umgebung — gigabytegross, lokal)
- `*.db` (lokale SQLite-Datenbank)
- `__pycache__/` (Python-Cache)

## Einrichtung Schritt für Schritt

### Variante A: Lokal (empfohlen zum Lernen)

```bash
# 1. Python-Version prüfen (≥ 3.11)
python --version

# 2. Virtual Environment anlegen
python -m venv .venv

# 3. Aktivieren
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows PowerShell

# 4. Dependencies installieren
pip install -r requirements.txt

# 5. .env vorbereiten
cp .env.example .env
# .env mit Editor öffnen, ANTHROPIC_API_KEY einfügen
```

### Was ist ein "Virtual Environment"?

Ein isolierter Python-Sandkasten **nur für dieses Projekt**. Pakete, die du hier installierst, kollidieren nicht mit deinem System-Python oder anderen Projekten.

**Analogie:** Wie eine eigene Kiste Lego, die nicht mit den Legos deiner Geschwister vermischt wird.

## Verifikation

Nach dem Setup solltest du folgendes tippen können:

```bash
python -c "import fastapi, anthropic, sqlmodel; print('OK')"
```

Ausgabe: `OK` → Phase 0 erfolgreich.
