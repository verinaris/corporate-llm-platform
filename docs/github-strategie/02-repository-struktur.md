# 02 — Die 6 angehefteten Repositories

> **Strategie:** Jedes der 6 Pins erzählt einen anderen Aspekt deiner
> Beratungskompetenz. Zusammen bilden sie ein **Beratungs-Portfolio** —
> nicht ein Coding-Portfolio.

---

## 🎯 Übersichtstabelle

| # | Repository | Funktion im Portfolio | Sichtbarkeit |
|---|---|---|---|
| 1 | `corporate-llm-platform` | **Substanz-Beweis** — echte Software | 🟢 Public |
| 2 | `ki-transformation-blueprint` | **Vorgehens-Modell** — Methodik | 🟢 Public |
| 3 | `ai-use-cases-sme` | **Konkrete Anwendungsbilder** — Use-Cases | 🟢 Public |
| 4 | `automation-workflows` | **Praxis-Bausteine** — wiederverwendbar | 🟢 Public |
| 5 | `it-governance-templates` | **Strukturierung** — RACI, Demand, Architektur | 🟢 Public |
| 6 | `thought-leadership` | **Haltung** — Whitepaper & Analysen | 🟢 Public |

---

## 1️⃣ corporate-llm-platform

```
Zweck:       Lebendiger Beweis, dass du KI-Plattformen nicht nur empfiehlst,
             sondern selbst bauen / orchestrieren kannst.
Zielgruppe:  Technische Entscheider, Recruiter mit Tiefe, Berater-Kollegen
Nutzen:      "Hat gemacht" statt "kann reden über"
```

### Inhalt
- Produktiv funktionierende KI-Plattform (FastAPI + Streamlit + ChromaDB + Ollama + Anthropic)
- Vollständige Phasen-Dokumentation (`docs/phase-X-*.md`)
- BACKLOG.md mit MoSCoW-Priorisierung
- Tests (88+ grüne Tests)
- Branchen-Plugin am Beispiel Pharma (HWG/AMG-Compliance)
- DSGVO/EU AI Act-Maßnahmen im Code dokumentiert

### Ordnerstruktur
```
corporate-llm-platform/
├── README.md                       ← Erste Sicht für Besucher
├── BACKLOG.md                      ← Zeigt strategisches Denken
├── docs/
│   ├── architecture.md
│   ├── phase-0-setup.md … phase-4-ollama.md
│   ├── branchen-architektur.md
│   └── github-setup.md
├── app/                            ← Backend
├── streamlit_app/                  ← Frontend
├── tests/
├── Dockerfile + docker-compose.yml
├── .env.example                    ← KEINE echten Keys
└── .gitignore                      ← data/ ausgeschlossen
```

### Was rein darf
✅ Code, Tests, Doku, Diagramme, Architektur-Entscheidungen
✅ Anonymisierte Beispiel-Outputs, Screenshots ohne Kundendaten
✅ Lessons Learned, Architektur-Trade-offs

### Was NIE rein darf
❌ Echte API-Keys, Tokens, Passwörter
❌ Echte PDF-Uploads aus deinem `data/`-Ordner
❌ Echte Kunden-Daten in Beispiel-Sammlungen
❌ Backup-Files der SQLite-Datenbank
❌ Server-Logs, Stack-Traces mit IP-Adressen

---

## 2️⃣ ki-transformation-blueprint

```
Zweck:       Dein Vorgehensmodell für KI-Einführungen sichtbar machen
Zielgruppe:  Geschäftsführer, IT-Leiter vor KI-Entscheidungen
Nutzen:      "Sie haben einen Plan, kein Hype"
```

### Inhalt
- 5-Phasen-Modell (Strategie → Use-Case → Pilot → Skalierung → Betrieb)
- Reifegrad-Assessment als Excel-Vorlage + Beschreibung
- Entscheidungs-Templates (Build vs. Buy, Cloud vs. lokal, …)
- Mermaid-Diagramme der typischen Ist/Soll-Zustände
- Glossar (BSI, EU AI Act, DSGVO-Begriffe — praxisnah erklärt)

### Ordnerstruktur
```
ki-transformation-blueprint/
├── README.md                        ← Methodik-Übersicht
├── 01-strategie/
│   ├── reifegrad-assessment.md
│   └── stakeholder-mapping.md
├── 02-use-cases/
│   ├── ideation-canvas.md
│   └── priorisierung-matrix.md
├── 03-pilot/
│   └── pilot-charter-template.md
├── 04-skalierung/
│   └── rollout-playbook.md
├── 05-betrieb/
│   ├── governance-board-template.md
│   └── kpi-katalog.md
├── glossar.md
└── diagramme/                      ← Mermaid-Files
```

### Was rein / nicht rein
✅ Generische Templates, Mermaid-Diagramme, Methodik-Erklärungen
❌ Konkrete Kundenfälle ohne Freigabe
❌ Vertrauliche Tools (z.B. proprietäre Reifegrad-Tools von Beratungen)

---

## 3️⃣ ai-use-cases-sme

```
Zweck:       Konkrete, KMU-taugliche KI-Anwendungsfälle aufzeigen
Zielgruppe:  Mittelständische Geschäftsführer ohne KI-Vorerfahrung
Nutzen:      "Was bringt mir KI konkret in meinem Betrieb?"
```

### Inhalt
- 15-20 Use-Cases mit einheitlicher Struktur:
  - Branche / Funktionsbereich
  - Problem
  - KI-Ansatz
  - Erwarteter Nutzen + Aufwand
  - Datenschutz-Hinweise (DSGVO/EU AI Act)
  - Empfohlene Tools / Modelle
- Gegliedert nach Branchen (Handwerk, Pharma, Energie, …)
  und Funktionen (Vertrieb, HR, Compliance, …)

### Ordnerstruktur
```
ai-use-cases-sme/
├── README.md
├── nach-branche/
│   ├── handwerk.md
│   ├── pharma.md
│   ├── energie.md
│   ├── steuerberatung.md
│   └── anwaltskanzlei.md
├── nach-funktion/
│   ├── vertrieb.md
│   ├── personalwesen.md
│   ├── compliance.md
│   └── kundenservice.md
└── template-use-case.md            ← Vorlage zum Erstellen neuer
```

### Was rein / nicht rein
✅ Generische Beschreibungen mit anonymisierten Branchenbeispielen
✅ Verweise auf öffentliche Studien (BSI, Bitkom, Fraunhofer)
❌ Echte Kennzahlen aus realen Kundenprojekten
❌ Names of customers, Mitarbeitenden oder spezifische Mengengerüste

---

## 4️⃣ automation-workflows

```
Zweck:       Praxis-Bausteine zeigen — du machst dir auch die Hände schmutzig
Zielgruppe:  IT-Leiter, Architekten, technische Berater-Kollegen
Nutzen:      "Sie reden nicht nur, sie liefern"
```

### Inhalt
- 5-10 sofort einsetzbare Automation-Bausteine:
  - n8n-Workflows (JSON-Exporte) für DSGVO-konforme Mailflüsse
  - GitHub-Actions-Templates (CI/CD für Python-Projekte)
  - Shell-Skripte für wiederkehrende Admin-Aufgaben (Backup, Log-Rotation)
  - Mermaid-Diagramme der Workflows
- Jeder Baustein hat eigene README mit Voraussetzungen, Installation, Risiken

### Ordnerstruktur
```
automation-workflows/
├── README.md
├── n8n/
│   ├── dsgvo-mailbox-cleanup/
│   └── lead-routing/
├── github-actions/
│   ├── python-quality-gate/
│   └── docker-build-push/
├── shell/
│   ├── postgres-backup/
│   └── log-rotation/
└── diagramme/
```

### Was rein / nicht rein
✅ Generische Workflows, anonymisierte JSON-Exporte
❌ Workflows mit echten Webhook-URLs, API-Tokens, internen Adressen
❌ Skripte, die spezifisch auf eine Kunden-Infrastruktur zugeschnitten sind

---

## 5️⃣ it-governance-templates

```
Zweck:       Strukturierungs-Kompetenz zeigen — "Sascha bringt Ordnung rein"
Zielgruppe:  IT-Leiter, CIO, Stabsstellen, Berater-Kollegen
Nutzen:      "Wir können sofort starten, hat fertige Vorlagen"
```

### Inhalt
- RACI-Matrizen für typische IT-Prozesse
- Demand-Management-Backlog-Templates (MoSCoW + INVEST, wie in der LLM-Platform!)
- Requirements-Catalog-Templates (funktional / nicht-funktional)
- Architektur-Decision-Records (ADR)-Templates
- Risikoregister-Templates
- DSGVO-Verarbeitungsverzeichnis-Template (Excel)

### Ordnerstruktur
```
it-governance-templates/
├── README.md
├── raci-matrizen/
│   ├── itil-incident-management.md
│   └── ai-governance-board.md
├── demand-management/
│   └── backlog-template.md
├── requirements/
│   ├── funktional-template.md
│   └── nicht-funktional-template.md
├── architecture/
│   └── adr-template.md
├── risk/
│   └── risikoregister-template.xlsx
└── compliance/
    └── dsgvo-vv-template.xlsx
```

### Was rein / nicht rein
✅ Generische, sofort verwendbare Vorlagen
✅ Erklärungen, wann welche Vorlage passt
❌ Ausgefüllte Vorlagen aus realen Mandaten

---

## 6️⃣ thought-leadership

```
Zweck:       Haltung und Tiefe zeigen — Bestandteil seriöser Beratung
Zielgruppe:  Entscheider, Recruiter, Medien, Kollegen
Nutzen:      "Hat eine Meinung, kann sie begründen"
```

### Inhalt
- 5-10 Whitepaper / Analysen (jeweils 3-8 Seiten):
  - "EU AI Act für KMU — praktische Checkliste"
  - "Lokales vs. Cloud-LLM: Entscheidungsmatrix für vertrauliche Daten"
  - "DSGVO-konforme RAG-Systeme — Quellen-Pflicht aus Art. 13 EU AI Act"
  - "Cloud-Souveränität: Hetzner / IONOS / STACKIT im Vergleich"
  - "Vom Pharma-Außendienst zum KI-Assistenten: Compliance-Stolpersteine"
- Format: Markdown im Repo, **optional** PDF-Export
- Klare Datierung — Inhalte veralten, das ist OK wenn transparent

### Ordnerstruktur
```
thought-leadership/
├── README.md                       ← Inhaltsverzeichnis nach Datum
├── 2026-q2/
│   ├── eu-ai-act-fuer-kmu.md
│   └── lokale-vs-cloud-llm.md
├── 2026-q3/
│   └── ...
└── _archiv/                        ← Überholte Texte
```

### Was rein / nicht rein
✅ Eigene Meinungen, begründet mit Quellen
✅ Zitate aus öffentlichen Studien (mit Quellenangabe!)
❌ Plagiate, ungekennzeichnete KI-Generate
❌ Politische / weltanschauliche Positionen ohne IT-Bezug
❌ Konkrete Kritik an namentlich genannten Unternehmen

---

## 🧭 Anheft-Reihenfolge (Pinned-Pins)

GitHub erlaubt max. 6 Pins. Reihenfolge ist wichtig — Besucher scannen
**von oben links nach unten rechts**:

```
┌─────────────────────────┬─────────────────────────┐
│ 1. corporate-llm-       │ 2. ki-transformation-   │
│    platform (Showcase)  │    blueprint (Methodik) │
├─────────────────────────┼─────────────────────────┤
│ 3. ai-use-cases-sme     │ 4. it-governance-       │
│    (Konkretisierung)    │    templates (Struktur) │
├─────────────────────────┼─────────────────────────┤
│ 5. automation-workflows │ 6. thought-leadership   │
│    (Hands-on)           │    (Haltung)            │
└─────────────────────────┴─────────────────────────┘
```

**Begründung:**
- Oben links = Aufmerksamkeits-Hotspot → **stärkster Trumpf** (Substanz-Beweis)
- Daneben das **Vorgehensmodell** — beantwortet "wie arbeitet Sascha?"
- Mittlere Reihe konkretisiert
- Untere Reihe rundet ab (Hands-on + Haltung)

---

## 📊 Repository-Reifegrad-Tabelle

Nicht alles muss von Tag 1 perfekt sein. Pragmatischer Reifegrad-Pfad:

| Repo | Minimum Viable (Phase 1) | Vollständig (Phase 3) |
|------|--------------------------|------------------------|
| corporate-llm-platform | Code + 1 README + .env.example | Phase-Docs vollständig, Tests grün, BACKLOG.md |
| ki-transformation-blueprint | README + 2 Templates | 5-Phasen-Modell komplett mit Diagrammen |
| ai-use-cases-sme | README + 5 Use-Cases | 15-20 Use-Cases, branchen+funktional gegliedert |
| automation-workflows | README + 1 Workflow | 5-10 Bausteine in 3 Kategorien |
| it-governance-templates | README + 3 Templates | 10+ Templates über 5 Kategorien |
| thought-leadership | README + 1 Whitepaper | 5+ datierte Analysen |

> **Empfehlung:** Phase 1 in den ersten 30 Tagen schaffen. Dann iterativ
> aufbauen — 1 Whitepaper / 2 Use-Cases pro Monat ist nachhaltig.
