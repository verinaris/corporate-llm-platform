# 05 — Security- & Compliance-Checkliste

> **Leitprinzip:** Vor jeder Veröffentlichung diese Checkliste durchlaufen.
> Lieber 20 Minuten investieren als 6 Monate Reputation reparieren.

---

## 🚨 Die Anti-Disaster-Regeln

Diese drei Dinge passieren häufig — und sind jedes Mal vermeidbar:

1. **API-Key in Repo** — *passiert mindestens 1× pro Jahr bei Devs ohne Disziplin*
2. **Echte Kunden-Datei in `data/`** — *passiert wenn `.gitignore` nicht stimmt*
3. **Personenbezogene Daten in Test-Fixtures** — *passiert wenn man "schnell" testet*

Die Checkliste unten verhindert genau diese Fälle.

---

## 🔍 Freigabe-Checkliste vor jeder Veröffentlichung

> Drucke diese Liste aus oder hänge sie in dein Repo als `RELEASE-CHECKLIST.md`.
> Vor jedem `git push` zu einem Public-Repo: alle Punkte ✅.

### 🔑 Secrets & Credentials

- [ ] **Keine API-Keys** im Code oder in Commit-Messages
- [ ] **`.env` ist in `.gitignore`** und wurde nie committet (auch nicht in Vergangenheit!)
- [ ] **`.env.example`** existiert mit Platzhaltern (`<DEIN_KEY_HIER>`)
- [ ] **Secret-Scan ausgeführt**:
  ```bash
  # Sucht in Git-History nach typischen Secret-Mustern
  git log --all -p | grep -iE "api[_-]?key|secret|token|password" | head -50
  ```
- [ ] **Kein hard-coded Passwort** (auch nicht "test123" in Tests — kommt schlecht in Code-Review)
- [ ] **JWT-Secret** wird aus Environment gelesen, nicht im Code
- [ ] **Cloud-Zugangsdaten** (AWS-Keys, Azure-SP-Credentials, GCP-Service-Accounts) sind in keinen Files
- [ ] **TLS-Zertifikate, Private-Keys (.pem, .key, .crt)** nicht im Repo

### 📂 Daten

- [ ] **`data/` ist in `.gitignore`** mit Ausnahme `data/README.md`
- [ ] **Keine echten PDFs / DOCX / XLSX** im Repo — auch nicht "zum Testen"
- [ ] **`uploads/`, `documents/`, `chroma/`** sind ausgeschlossen
- [ ] **Datenbank-Dateien** (`*.db`, `*.sqlite`, `*.sqlite3`) ausgeschlossen
- [ ] **Backup-Dateien** (`*.bak`, `*.dump`) ausgeschlossen
- [ ] **Log-Dateien** (`*.log`, `logs/`) ausgeschlossen
- [ ] **Browser-History / Session-Daten** in Tests anonymisiert

### 🧑 Personenbezogene Daten (DSGVO)

- [ ] **Keine echten Namen** in Test-Fixtures (`Max Mustermann`, `Erika Musterfrau` OK)
- [ ] **Keine echten E-Mail-Adressen** (`@example.com` / `@example.org` nutzen, RFC 2606)
- [ ] **Keine echten Telefonnummern**
- [ ] **Keine echten Adressen** (außer fiktiven)
- [ ] **Keine echten Geburtsdaten**
- [ ] **Patientendaten / Mandantendaten / Steuerdaten**: NIEMALS
- [ ] **Mitarbeiter-Namen aus Kundenprojekten**: NIEMALS

### 🏢 Kundenbezogene Inhalte

- [ ] **Keine Kunden-Logos** ohne explizite Schriftform-Freigabe
- [ ] **Keine Kunden-Namen** in Repo-Namen, Commit-Messages, Issues
- [ ] **Keine Architektur-Diagramme mit Kunden-internen Systemen**
  (auch nicht "anonymisiert" — Branchen-Insider erkennen es)
- [ ] **Keine Source-Code-Snippets aus Kundenprojekten** (auch nicht "stark verändert")
- [ ] **Keine internen Email-Verteiler oder Slack-Channel-Namen**

### 📜 Lizenzen & Urheberrecht

- [ ] **Eigener Code:** Lizenz gewählt und in `LICENSE` gesetzt (MIT, Apache 2.0, CC BY 4.0)
- [ ] **Fremder Code:** Lizenz-kompatibel? Quelle in Datei-Header
- [ ] **Bilder / Grafiken:** Eigene oder lizenzfrei (Creative Commons, eigenes Werk)
- [ ] **Mermaid/PlantUML-Diagramme:** eigene Erstellung
- [ ] **Zitate** in Whitepaper: max. 15 Wörter pro Quelle, mit Verweis

### 🔧 Code-Qualität (für Public-Repos)

- [ ] **README** ist verständlich (auch ohne Vorwissen)
- [ ] **Setup-Anleitung** funktioniert auf frischem System
- [ ] **`requirements.txt` / `package.json`** ist aktuell
- [ ] **Keine TODO/FIXME** mit kritischen Hinweisen ("TODO: Auth fixen vor Prod")
- [ ] **Tests laufen grün** (zumindest die existierenden)
- [ ] **Keine `print("DEBUG: ...")`-Reste** im Code

### 📝 Metadaten & Konfiguration

- [ ] **Repo-Beschreibung** ist gesetzt (1-2 Zeilen)
- [ ] **Topics** sind sinnvoll (5-10, siehe `01-profil-strategie.md`)
- [ ] **License** ist im Repo-Header sichtbar
- [ ] **`README.md`** beginnt mit klarem Wertversprechen
- [ ] **Badges** sind aktuell (keine "Build: failing" wenn's grün ist)

---

## 🛡️ Compliance-Themen im Detail

### DSGVO

| Was zu beachten | Wo prüfen |
|---|---|
| Personenbezogene Daten in Beispielen? | Tests, Fixtures, README-Screenshots |
| Cookie-Hinweise / Telemetrie aktiviert? | Streamlit-Config, Frontend-Skripte |
| Audit-Log vorhanden? | Strukturelle Frage, kein Repo-Item |
| DSFA (Folgenabschätzung) erforderlich? | Nur für produktive Systeme |

### EU AI Act (gilt seit 2024)

| Was zu beachten | Konsequenz |
|---|---|
| Klassifizierung des Systems (Risiko-Stufe)? | High-Risk → eigene Doku-Pflichten |
| Transparenz-Pflicht (Art. 13) | RAG: Quellenangaben Pflicht ✅ in Plattform |
| Human-Oversight-Anforderung | UI muss klar machen: KI-Antwort, nicht Faktenwahrheit |
| Logging für Auditierbarkeit | Token-Logs ja, aber DSGVO-konform |

### BSI-Grundschutz (für Bundeswehr-nahe / öffentliche Auftraggeber)

| Empfehlung | Status in Corporate LLM Platform |
|---|---|
| Verschlüsselung at-rest | TODO Phase 6 (PostgreSQL TDE) |
| Verschlüsselung in-transit | HTTPS via Caddy/Traefik in Phase 6 |
| Multi-Faktor-Auth | Wishlist (`2FA`) |
| Schlüsselverwaltung | JWT-Secret aus Vault — in Phase 6 |
| Backup + Restore-Test | TODO Phase 6 |
| Pentest | Wishlist |

---

## 🔄 Automatische Schutz-Mechanismen einrichten

### 1. Pre-commit-Hook für Secret-Detection

```bash
pip install detect-secrets
cd dein-repo
detect-secrets scan > .secrets.baseline
```

In `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 2. GitHub Secret Scanning aktivieren

Settings → Code security → "Secret scanning" + "Push protection" aktivieren.
GitHub blockiert dann Pushes, wenn ein API-Key-Muster erkannt wird.

### 3. Dependabot für Schwachstellen-Alerts

Settings → Code security → Dependabot alerts + security updates aktivieren.

### 4. CODEOWNERS-File für sensible Bereiche

In `.github/CODEOWNERS`:
```
# Sicherheitsrelevante Bereiche brauchen Sascha-Review
/app/auth/        @<dein-username>
/app/config.py    @<dein-username>
*.env*            @<dein-username>
```

---

## 🚒 Notfall-Plan: Secret ist doch leaked

Wenn du **nach** einem Push merkst, dass ein Secret im Repo gelandet ist:

1. **Sofort den Key rotieren** beim Provider (Anthropic, GitHub, etc.)
2. **Git-History bereinigen:**
   ```bash
   pip install git-filter-repo
   git filter-repo --invert-paths --path .env
   git push --force --all
   git push --force --tags
   ```
3. **GitHub Support kontaktieren** für endgültige Entfernung
4. **Logs prüfen** beim Provider: wurde der Key genutzt?
5. **Vorfall dokumentieren** — auch für eigene DSGVO-Pflichten

> ⚠️ **Wichtig:** Ein Force-Push allein reicht NICHT. Caches, Forks und
> GitHubs eigene Archive können das Secret noch enthalten. Rotation ist Pflicht.

---

## ✅ Mini-Skript: Selbst-Audit eines Repos

```bash
#!/usr/bin/env bash
# Prüft ein Repo grob auf typische Probleme

set -e
REPO_PATH="${1:-.}"
cd "$REPO_PATH"

echo "🔍 Auditing: $(pwd)"

# Test 1: .env in gitignore?
if grep -q "^\.env$\|^\.env\.\*" .gitignore 2>/dev/null; then
    echo "  ✅ .env in .gitignore"
else
    echo "  ❌ .env NICHT in .gitignore"
fi

# Test 2: data/ in gitignore?
if grep -q "^data/$\|^data/" .gitignore 2>/dev/null; then
    echo "  ✅ data/ in .gitignore"
else
    echo "  ❌ data/ NICHT in .gitignore"
fi

# Test 3: Secrets in History?
SECRETS=$(git log --all -p 2>/dev/null | grep -ciE "ANTHROPIC_API_KEY=|sk-ant-api|jwt_secret=[a-zA-Z0-9]" | head -1)
if [ "$SECRETS" -gt 0 ]; then
    echo "  ⚠️  Mögliche Secrets in Git-History (manuell prüfen!)"
else
    echo "  ✅ Keine offensichtlichen Secrets in History"
fi

# Test 4: README vorhanden?
if [ -f "README.md" ]; then
    echo "  ✅ README.md existiert"
else
    echo "  ❌ README.md fehlt"
fi

# Test 5: LICENSE vorhanden?
if [ -f "LICENSE" ]; then
    echo "  ✅ LICENSE existiert"
else
    echo "  ⚠️  LICENSE fehlt — wichtig für Public-Repos"
fi

echo "🏁 Audit fertig. Manuelle Prüfung der ⚠️ und ❌ Punkte empfohlen."
```

Speichern als `~/bin/repo-audit.sh`, ausführbar machen, dann:
```bash
repo-audit.sh ~/path/to/repo
```
