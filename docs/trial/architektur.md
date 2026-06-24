# 💎 Trial-Mechanismus — Architektur-Skizze

**Stand:** Juni 2026
**Autor:** Sascha Kern + Claude (Sparring)
**Status:** Konzept-Skizze (noch nicht implementiert)
**Ziel:** 7-Tage-Trial mit sanftem Hinweis nach Ablauf — Open-Source-konform

---

## 🎯 Strategischer Kontext

**Verinaris ist Open Core:**
- Kern: Open Source (FastAPI, RAG, Auth, etc.)
- Premium-Features: später als separate Module (Phase 2)

**Was dieser Trial NICHT ist:**
- ❌ Keine Lizenzschutz-DRM (wäre Open-Source-feindlich)
- ❌ Keine Funktions-Sperre nach 7 Tagen
- ❌ Kein Phone-Home zu verinaris-Server

**Was dieser Trial IST:**
- ✅ Freundlicher Hinweis im UI nach 7 Tagen
- ✅ Vertriebs-Trigger ("Kontakt für Lizenz")
- ✅ Transparenter Mechanismus (User sieht den Code)
- ✅ Vorbereitung für späteres Lizenz-System

---

## 🏗 Architektur-Übersicht

\`\`\`mermaid
graph TB
    User[👤 User] --> UI[💻 Streamlit]
    UI --> API[⚙️ FastAPI]
    API --> Trial[📅 TrialService]
    Trial --> DB[(🗄 platform.db)]

    UI -->|GET /api/trial/status| API
    API -->|read installed_at| DB
    API -->|compute remaining days| Trial
    Trial -->|TrialStatus response| UI
    UI -->|render banner| User

    style Trial fill:#fff9c4
    style DB fill:#c8e6c9
\`\`\`

**Kern-Idee:** Beim ersten App-Start wird das **Installations-Datum** in die DB geschrieben. Danach prüft das Frontend bei jedem Login, ob die 7 Tage noch laufen.

---

## 🧩 Komponente 1: Datenbank-Modell

### Neue Tabelle: trial_state

\`\`\`python
# app/models.py (erweitern)

class TrialState(SQLModel, table=True):
    """Verfolgt Installations-Datum und Lizenz-Status der Verinaris-Instanz."""

    id: int | None = Field(default=None, primary_key=True)
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # = installed_at + 7 Tage
    license_key: str | None = Field(default=None, max_length=128)
    license_valid_until: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
\`\`\`

**Wichtige Entscheidung:** **Nur 1 Zeile** in dieser Tabelle — sie repräsentiert die Verinaris-Instanz als Ganzes (nicht pro User!).

---

## 🧩 Komponente 2: TrialService

Status-Berechnung mit 4 Zuständen:

- **ACTIVE** — > 24h verbleibend
- **EXPIRING_SOON** — < 24h verbleibend
- **EXPIRED** — Testphase beendet
- **LICENSED** — Aktive Lizenz vorhanden

Pro Status eine deutsche Nachricht für den UI-Banner.

---

## 🧩 Komponente 3: API-Endpoint

\`\`\`
GET /api/trial/status
→ {
    "status": "active" | "expiring_soon" | "expired" | "licensed",
    "days_remaining": 4,
    "hours_remaining": 96,
    "installed_at": "2026-06-22T14:32:00",
    "expires_at": "2026-06-29T14:32:00",
    "message": "Verinaris Testversion — 4 Tage verbleibend.",
}
\`\`\`

→ **Bewusst ohne Auth** — auch das Login-Fenster muss den Status anzeigen können.

---

## 🧩 Komponente 4: Streamlit-Banner

Anzeige **oben in jeder Seite** (Chat, Stats, Documents, Admin):

- 🟢 **active** → st.info
- 🟡 **expiring_soon** → st.warning
- 🔴 **expired** → st.error
- ✅ **licensed** → st.success

---

## 🎨 UX-Beispiele

### Aktive Testphase (Tag 3)
🟢 Verinaris Testversion — 4 Tage verbleibend.

### Letzter Tag (Tag 7, < 24h)
🟡 ⚠️ Letzter Tag der Testphase (18h verbleibend). Kontakt für Lizenz: sascha@verinaris.de

### Abgelaufen (Tag 8+)
🔴 Die 7-tägige Testphase ist beendet. Für die weitere Nutzung kontaktieren Sie sascha@verinaris.de

### Mit Lizenz
✅ Lizenzierte Version aktiv.

---

## ❓ Offene Fragen

### 1. Wo Banner anzeigen?
**Entscheidung:** Oben in jeder Seite (auch Chat, Stats, Doc)

### 2. Login-Fenster bei expired?
**Empfehlung:** Login funktioniert weiter — sanfter Hinweis ist die Regel.

### 3. Lizenz-Key Format
Phase 2-Frage. Für jetzt: license_key-Feld in DB lassen, aber nicht implementieren.

### 4. Wann wird installed_at gesetzt?
**Empfehlung:** Beim ALLERSTEN Start der App — automatisch.

---

## 🎯 Implementierungs-Reihenfolge

1. **Model + Migration** → 30 Min
2. **TrialService** → 45 Min
3. **API-Endpoint** → 20 Min
4. **Streamlit-Banner** → 30 Min
5. **Tests** → 30 Min
6. **README + Doku** → 15 Min

**Total:** ~2.5h

---

## ⚠️ Wichtige Hinweise

### Was darf NICHT passieren
- ❌ Keine harte Sperre — Chat muss weiter funktionieren
- ❌ Kein Phone-Home — keine externe API-Calls
- ❌ Kein Crypto-Check — Banner muss leicht entfernbar sein

### README-Eintrag (Open Core Modell)

Verinaris ist Open Source unter MIT-Lizenz. Die Plattform startet mit
einer 7-tägigen Testphase, nach der ein freundlicher Hinweis im UI
erscheint.

Da Verinaris Open Source ist, können Sie den Hinweis selbstverständlich
selbst entfernen — wir bitten Sie aber, in regulierten Branchen den
**Verinaris Commercial Plan** zu nutzen, der professionellen Support,
Schulungen und branchen-spezifische Profile beinhaltet.

→ Kontakt: sascha@verinaris.de

---

## 🚀 Phase 2 — Was kommt später

Wenn der erste zahlende Kunde da ist:
- Lizenz-Server (verinaris-license-server)
- Lizenz-Key-Generator (HMAC-signiert)
- Streamlit: Lizenz-Key-Eingabe-Feld
- Admin-UI für Lizenz-Verwaltung
- Branchen-Profile als private Module (verinaris-enterprise)

→ **Heute nicht.** Erst nach erstem Kunden.
