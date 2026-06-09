# 📋 Backlog — Corporate LLM Platform

**Stand:** Phase 2b + Quick Wins (BFSG/Cloud)
**Methode:** MoSCoW + INVEST

---

## 🎨 Legende

**Status:** `[ ]` offen · `[x]` erledigt · 🚧 in Arbeit
**Priorität:** 🔴 Must · 🟡 Should · 🟢 Could · ⚪ Won't (yet)
**Typ:** `[F]` funktional · `[NF]` nichtfunktional · `[B]` branchenspezifisch

---

## ✅ Erledigt

- [x] FastAPI-Backend (`/health`, `/chat`, `/stats`)
- [x] Anthropic-Claude-Integration mit Multi-Modell-Auswahl
- [x] Token-Logging + Kostenberechnung
- [x] Provider-Abstraktion + Branchen-Plugin-Gerüst
- [x] **Phase 2a:** Auth-Backend (JWT, bcrypt, 4 Rollen, Bootstrap-Admin)
- [x] **Phase 2a:** User-Verwaltung (CRUD nur Admin)
- [x] **Phase 2b:** Streamlit-Frontend (Login, Chat, Stats)
- [x] **Quick Win:** Sprache `de` + Focus-Ring
- [x] **Quick Win:** Streamlit-Theme + Telemetrie aus
- [x] **Quick Win:** Production-Validation in `.env`
- [x] **Quick Win:** Anthropic-Region konfigurierbar
- [x] **Quick Win:** Dockerfile + docker-compose.yml + .dockerignore
- [x] Strukturierte Doku pro Phase
- [x] Versionskontrolle via Git/GitHub

---

## 📋 Phase 2c — Pharma-Plugin lebendig (als nächstes)

### Funktional
- [ ] 🔴 `[F]` HWG/AMG-konformer Pharma-System-Prompt
- [ ] 🔴 `[F]` Pharma-Disclaimer wird automatisch angehängt
- [ ] 🔴 `[F]` Im /chat-Endpoint: User-Branche → Plugin auswählen
- [ ] 🟡 `[F]` Streamlit zeigt "Pharma-Mode aktiv"
- [ ] 🟡 `[F]` UI-Disclaimer im Chat sichtbar

### Nichtfunktional
- [ ] 🔴 `[NF]` Test: Pharma-User bekommt Disclaimer, Generic-User nicht
- [ ] 🟡 `[NF]` Plugin-Mechanik dokumentieren

---

## 📋 Phase 3 — RAG

- [ ] 🔴 `[F]` PDF-Upload + ChromaDB-Indexierung
- [ ] 🔴 `[F]` Antwort mit Quellenangabe
- [ ] 🟡 `[F]` Mehrere Sammlungen (HR, Technik, Marketing)
- [ ] 🟢 `[F]` OCR für Scans
- [ ] 🔴 `[NF]` Quellenangabe = Pflicht (EU AI Act Art. 13)
- [ ] 🔴 `[NF]` Dokumente bleiben lokal
- [ ] 🟡 `[NF]` Lokales Embedding-Modell

---
## 📋 Phase 3c — Document-Storage UX-Verbesserungen ✅
Funktional

- [x] 🟡 `[F]` Upload-Fortschrittsanzeige mit Phasen-Status (NDJSON-Stream)
- [x] 🟡 `[F]` Phasen-Statusmeldung während Upload:
  "Hochladen → PDF lesen → Chunks erstellen → Embeddings → Fertig"
- [x] 🟢 `[F]` Sammlung-Beschreibungen + Tags
- [x] 🟢 `[F]` Erweiterter Quellen-Kontext + PDF-Download in Chat
- [ ] 🟢 `[F]` PDF-Inline-Vorschau (Browser-Viewer) — verschoben auf 3d
- [ ] 🟢 `[F]` Versionierung von Dokumenten (alte Version archivieren bei Re-Upload)

Nichtfunktional

- [x] 🟡 `[NF]` Streaming-Response (NDJSON) für Phasen-Updates
- [ ] 🟢 `[NF]` Background-Job-Queue (z.B. mit RQ oder Celery)
  für Uploads > 100 MB, damit Browser nicht blockiert

---

## 📋 Phase 3d — Multi-Format-Upload (neu, geplant)

Aktuell nur PDF. Erweiterung um weitere Formate:

**Text-Formate (einfach):**
- [ ] 🟡 `[F]` `.txt` Plain Text
- [ ] 🟡 `[F]` `.md` Markdown
- [ ] 🟡 `[F]` `.docx` Word (via `python-docx`)
- [ ] 🟡 `[F]` `.xlsx` Excel (via `openpyxl`)
- [ ] 🟢 `[F]` `.epub` E-Books (via `ebooklib`)

**Transkripte:**
- [ ] 🟢 `[F]` `.srt`, `.vtt` Untertitel-Formate
- [ ] 🟢 `[F]` Markdown-Transkripte

**OCR (mittlere Komplexität):**
- [ ] 🟢 `[F]` Gescannte PDFs (Bilder ohne Text-Layer)
- [ ] 🟢 `[F]` Bilder mit Text (`.png`, `.jpg`) via `pytesseract`

**Audio/Video (eigene Phase 7 — lokale ML-Pipeline):**
- [ ] ⚪ `[F]` MP3/WAV Audio → Whisper-Transkription
- [ ] ⚪ `[F]` MP4/MOV Video → ffmpeg + Whisper

> **Hinweis:** Audio/Video braucht GPU oder dauert auf CPU. Background-Job-Queue 
> wird Pflicht. Embeddings können pro Stunde Video mehrere GB werden.

---

## 📋 Phase 4 — Multi-LLM-Routing

- [x] 🔴 `[F]` Ollama-Adapter (lokales Modell) ✅
- [x] 🔴 `[F]` Dynamisches Modell-Dropdown (Cloud + Lokal) ✅
- [x] 🔴 `[F]` Endpoint `/models/available` ✅
- [x] 🔴 `[F]` Pricing $0 für lokale Modelle ✅
- [ ] 🟡 `[F]` OpenAI-Adapter (analog zu OllamaClient — bei Bedarf)
- [ ] 🟡 `[F]` Regel-Router (sensible Daten → automatisch Ollama) — braucht PII-Filter
- [ ] 🟢 `[F]` Fallback-Logik (Anthropic down → OpenAI/Ollama)
- [ ] 🟢 `[F]` Streaming-Responses (wortweise statt komplett am Ende)
- [ ] 🟢 `[F]` Modell-Vergleichs-Modus (parallel an mehrere Provider)

---

## 📋 Phase 5a — Businessplan-Generator ✅ (Grundkomponente für alle Kunden)

**Inspiriert durch Verinaris-MVP, in unsere Architektur integriert.**

### Funktional
- [x] 🔴 `[F]` Branchenübergreifender Businessplan-Generator
- [x] 🔴 `[F]` Template-System (KMU Standard, Verinaris-Beispiel)
- [x] 🟡 `[F]` 3-Jahres-Finanz-Forecast
- [x] 🟡 `[F]` Härtungs-Checks IHK/HwK/Bank/BA/Compliance/Vertrieb
- [x] 🟡 `[F]` Fördermittel-Matching mit Regional-Filter
- [x] 🟡 `[F]` 4-KPI-Scorecard
- [x] 🟡 `[F]` LLM-Executive-Summary (Anthropic ODER Ollama)
- [x] 🟢 `[F]` Word/Excel/PDF-Export

### Nichtfunktional
- [x] 🟡 `[NF]` 19 Tests grün
- [x] 🟡 `[NF]` Plan-Persistenz in zentraler DB
- [x] 🔴 `[NF]` Rollenbasiert: Admin sieht alle Pläne, User nur eigene

### Geplante Erweiterungen (Phase 5b+)
- [x] 🟡 `[F]` Pharma-Beratung & Vertrieb Branchen-Vorlage ✅ (Phase 5b)
- [x] 🟡 `[F]` Industry-Checks-System (dispatch nach Branche) ✅ (Phase 5b)
- [x] 🟡 `[F]` Industry-Fördermittel (pharma-spezifisch) ✅ (Phase 5b)
- [x] 🔴 `[F]` Branchen-Profile als 1. Klasse Bürger ✅ (Phase 5c)
  - GET/PUT `/profile/me/branch` API
  - Sidebar mit Branchen-Wähler
  - Businessplan-Vorlagen nach User-Branche gefiltert
  - Zentrales Mapping-Modul `app/branches/profiles.py`
- [ ] 🟡 `[F]` Weitere Branchen-Vorlagen: Steuerberatung, Anwalt, Energie, Handwerk
- [ ] 🟢 `[F]` RAG-Integration: Marktanalyse-Sammlung automatisch verlinken
- [ ] 🟢 `[F]` Plan-Versionierung (alte Stände bewahren)
- [ ] 🟢 `[F]` Live-Charts in Streamlit (statt nur Tabellen)
- [ ] 🟢 `[F]` Vergleich mehrerer Pläne nebeneinander

---

## 📋 Phase 5 — Admin-Dashboard (teilweise erledigt durch Phase 6a)

### Phase 6a — Compliance-Pflicht ✅ ERLEDIGT
- [x] 🔴 `[F]` Audit-Log: Datenmodell + Service ✅
- [x] 🔴 `[F]` Audit-Hooks (Login, Branche, Plan-Save/Delete, DSGVO) ✅
- [x] 🔴 `[F]` Audit-Log-Ansicht (Admin/Compliance) ✅
- [x] 🔴 `[F]` Daten-Lösch-Funktion (DSGVO Art. 17) mit Pseudonymisierung ✅
- [x] 🟢 `[F]` DSGVO Art. 15 Datenexport ✅
- [x] 🟡 `[NF]` 16 Tests grün ✅

### Phase 6b — Marketing-Power (offen)
- [ ] 🟡 `[F]` Token-/Kosten-Charts
- [ ] 🟡 `[F]` CSV-/Excel-Export Token-Daten
- [ ] 🟡 `[F]` User-Verwaltung im Frontend (statt nur Admin-CLI)
- [ ] 🟡 `[F]` **Täglicher EZB-Referenzkurs-Fetch** für USD→EUR-Umrechnung
  - Quelle: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
  - Cache: 24h (täglich um 16:00 CET aktualisiert)
  - Fallback: statischer Wert aus `config.py` wenn Fetch fehlschlägt
  - Optional: historische Kurse für Backdating (z.B. Rechnung für Vormonat)

### Phase 6c — Audit-Erweiterungen (offen, später)
- [ ] 🟢 `[F]` Weitere Audit-Hooks (Documents, Chat, Collections, Plan-Update/Export)
- [ ] 🟢 `[NF]` Automatische Retention-Policy für Audit-Log (10 Jahre)
- [ ] 🟢 `[F]` Anomalie-Detection (z.B. 5x failed login → Alert)

---

## 📋 Phase 6 — Deployment & Cloud (NEU)

### Container & Orchestrierung
- [ ] 🔴 `[F]` Dockerfile für **Streamlit** als zweiter Service
- [ ] 🔴 `[F]` docker-compose mit Backend + Frontend + Reverse Proxy
- [ ] 🔴 `[F]` HTTPS via Caddy oder Traefik
- [ ] 🟡 `[F]` Kubernetes-Manifeste (Deployment, Service, Ingress)
- [ ] 🟢 `[F]` Helm-Chart für KMU-Self-Hosting

### Datenbank-Migration
- [ ] 🔴 `[F]` **PostgreSQL** statt SQLite (mit Alembic-Migrations)
- [ ] 🔴 `[F]` Migration-Skript für bestehende SQLite-Daten
- [ ] 🟡 `[F]` Connection-Pooling

### Anthropic EU-Region
- [ ] 🔴 `[NF]` `ANTHROPIC_BASE_URL` auf EU-Endpoint aktivieren
- [ ] 🔴 `[NF]` AVV (Auftragsverarbeitungsvertrag) mit Anthropic
- [ ] 🟡 `[NF]` DSGVO-Verarbeitungsverzeichnis dokumentieren

### Production-Härtung
- [ ] 🔴 `[NF]` `APP_ENV=production`, `APP_DEBUG=false`
- [ ] 🔴 `[NF]` JWT-Secret aus Provider-Vault
- [ ] 🔴 `[NF]` CORS streng konfiguriert
- [ ] 🔴 `[NF]` Rate-Limiting (slowapi)
- [ ] 🟡 `[NF]` Pentest

### Monitoring & Observability
- [ ] 🟡 `[F]` Strukturiertes Logging (JSON, structlog)
- [ ] 🟡 `[F]` Prometheus-Metrics-Endpoint
- [ ] 🟢 `[F]` Grafana-Dashboard
- [ ] 🟢 `[F]` Sentry für Error-Tracking

### Backup & DR
- [ ] 🔴 `[NF]` Automatisches DB-Backup (täglich)
- [ ] 🟡 `[NF]` Restore-Test

### Provider-Auswahl (EU)
- [ ] 🟡 `[NF]` Hetzner Cloud / IONOS / STACKIT / Scaleway evaluieren
- [ ] 🟢 `[NF]` Lasttest

---

## 📋 Phase 7 — Agent-Architektur (geplant)

> **Ziel:** Von "Chatbot mit RAG" zu "intelligentem Assistent mit Tool-Use"
> hin zu "Multi-Step-Agent mit Human-in-the-Loop". Bewusst schrittweise.
>
> **Wichtig:** Für regulierte Branchen (Pharma, Anwalt, Steuer, Bundeswehr-nah)
> bleibt **Human-in-the-Loop Pflicht** — kein vollautonomer Versand,
> keine selbstständigen Compliance-Entscheidungen. Volle Autonomie wäre
> ein Compliance-Killer in deinen Zielbranchen.

### Phase 7a — Tool-Calling-Grundlage (~2 Wochen)
- [ ] 🟡 `[F]` Tool-Registry-Architektur (`app/tools/` mit BaseTool-Klasse)
- [ ] 🟡 `[F]` Anthropic Tool-Use (`tools`-Parameter im API-Call)
- [ ] 🟡 `[F]` Ollama Tool-Use (qwen2.5+, llama3.1+ unterstützen es)
- [ ] 🟡 `[F]` Erste 5 Tools:
  - `search_documents(query, collection)` — RAG-Suche
  - `web_search(query)` — externe Recherche
  - `generate_pdf_report(content, template)` — PDF-Export
  - `calculate_date(expression)` — Datum-Berechnung
  - `query_audit_log(filter)` — Compliance-Abfrage
- [ ] 🟡 `[F]` Rollen-basierte Tool-Berechtigungen (welche Rolle darf was)
- [ ] 🟡 `[F]` Tool-Calls im Audit-Log mitloggen
- [ ] 🟢 `[F]` UI-Erweiterung: "🛠 Werkzeug-Nutzung" anzeigen im Chat

### Phase 7b — Multi-Step-Agents (~4 Wochen)
- [ ] 🟡 `[F]` Agent-Loop (Plan → Execute → Observe → Adjust)
- [ ] 🟡 `[F]` Session-Memory (kurzfristig, in DB pro Konversation)
- [ ] 🟢 `[F]` Long-Term-Memory (Erkenntnisse pro Mandant/Kunde)
- [ ] 🔴 `[F]` **Human-in-the-Loop**: Genehmigungs-Workflow vor kritischen Aktionen
- [ ] 🟡 `[F]` Step-Limit + Recovery (Abbruch nach N Schritten oder bei Fehler)
- [ ] 🟢 `[F]` Streamlit-UI: Agent-Plan visualisieren, Schritt-für-Schritt-Approval

### Phase 7c — Branchen-Agent-Templates
- [ ] 🟡 `[F][B]` Pharma-Außendienst-Assistent (HWG-konform, kein autonomer Versand)
- [ ] 🟢 `[F][B]` Steuerberater-Buchungsvorschlag (DATEV-Integration)
- [ ] 🟢 `[F][B]` Anwalts-Aktenrecherche (Mandant-Mandant-Trennung Pflicht)
- [ ] 🟢 `[F][B]` Business-Plan-Generator (KMU-Schema)
- [ ] ⚪ `[F][B]` Energie-Lastprognose-Agent

### Nichtfunktional
- [ ] 🔴 `[NF]` **Compliance-Check vor jedem Tool-Call** (PII-Filter, Branchen-Regeln)
- [ ] 🔴 `[NF]` Audit-Trail: jeder Agent-Schritt mit Input/Output speicherbar (DSGVO)
- [ ] 🟡 `[NF]` Sandbox-Modus für Agenten ohne Außenwirkung (Dry-Run)
- [ ] 🟡 `[NF]` Token-Budget pro Agent-Lauf (Kostenkontrolle)

> **Architektur-Hinweis:** Bewusst KEIN externes Framework (LangChain,
> AutoGen, CrewAI). Selbst-gebauter dünner Wrapper um Anthropic/Ollama
> Tool-Use behält Kontrolle, Verständnis und langfristige Wartbarkeit.

---

## 🌐 Querschnittsanforderungen

### Compliance & Datenschutz
- [ ] 🔴 `[NF]` EU AI Act Art. 13: KI-Transparenz-Hinweis
- [ ] 🔴 `[NF]` DSGVO Art. 30: Verarbeitungsverzeichnis
- [ ] 🔴 `[NF]` DSGVO Art. 17: Recht auf Löschung
- [ ] 🔴 `[NF]` DSGVO Art. 25: Privacy by Design + by Default
- [x] `[NF]` Streamlit-Telemetrie deaktiviert ✓
- [ ] 🟡 `[NF]` Anthropic EU-Region in Produktion
- [ ] 🟡 `[NF]` AVV mit Anthropic
- [ ] 🟢 `[NF]` Vollständig lokaler Modus via Ollama

### Accessibility — BFSG / EAA / WCAG 2.1 AA (NEU)
- [x] `[NF]` HTML-Sprache `lang="de"` ✓
- [x] `[NF]` Focus-Ring sichtbar (WCAG 2.4.7) ✓
- [x] `[NF]` Kontrastreicher Default-Theme (WCAG 1.4.3) ✓
- [ ] 🔴 `[NF]` Vollständige Tastatur-Navigation aller Workflows
- [ ] 🔴 `[NF]` Screen-Reader-Test (VoiceOver, NVDA)
- [ ] 🟡 `[NF]` Lighthouse + axe-core Audit
- [ ] 🟡 `[NF]` Skip-to-Content-Link
- [ ] 🟢 `[NF]` Hoher Kontrast-Modus
- [ ] 🟢 `[NF]` Zoomfest bis 200%
- [ ] ⚪ `[NF]` Bei B2C-Vermarktung: Konformitätserklärung
- [ ] ⚪ `[NF]` Wechsel zu Next.js + shadcn/ui für vollen WCAG-Support

### Sicherheit
- [x] `[NF]` API-Keys nie loggen ✓
- [x] `[NF]` Production-Validation in config.py ✓
- [ ] 🔴 `[NF]` HTTPS in Produktion
- [ ] 🟡 `[NF]` Input-Validierung gegen Prompt-Injection
- [ ] 🟡 `[NF]` Sicherheits-Header (CORS, CSP, HSTS)
- [ ] 🟢 `[NF]` Pentest

### Performance
- [ ] 🟡 `[NF]` P95-Antwortzeit < 5s
- [ ] 🟡 `[NF]` Streaming-Antworten
- [x] `[NF]` Async-Architektur (FastAPI) ✓

### Wartbarkeit
- [ ] 🟡 `[NF]` Test-Coverage > 60%
- [ ] 🟡 `[NF]` Type Hints durchgängig (mypy)
- [ ] 🟡 `[NF]` Code-Style: Ruff + Black

---

# 🏢 Branchenmodule (KMU)

## 💊 Pharma-Außendienst (Phase 2c+)

### Regulatorik
| Bereich | Quelle |
|---------|--------|
| Werbung | HWG |
| Arzneimittel | AMG |
| Behörden | EMA / BfArM |
| Branche | FSA-Kodex |
| Datenschutz | DSGVO Art. 9 |
| KI | EU AI Act (ggf. High-Risk) |
| Barrierefreiheit | BFSG (bei B2C-Tools) |

### Funktional
- [ ] 🔴 `[F][B]` Fachinformations-Recherche per RAG
- [ ] 🔴 `[F][B]` Wechselwirkungs-Check
- [ ] 🔴 `[F][B]` Medikamentenplan/Therapieschemata
- [ ] 🔴 `[F][B]` Studien-Recherche
- [ ] 🟡 `[F][B]` Arztbesuch-Vorbereitung (NIE Patientendaten)
- [ ] 🟡 `[F][B]` HWG/AMG-Compliance-Check
- [ ] 🟡 `[F][B]` Aggregierte Kollektiv-Analyse (anonym only)
- [ ] 🟢 `[F][B]` Pharmakovigilanz-Hinweis-Generator

### Nichtfunktional
- [ ] 🔴 `[NF][B]` Pflicht-Disclaimer
- [ ] 🔴 `[NF][B]` PII-Detektor blockiert personenbezogen
- [ ] 🔴 `[NF][B]` Quellen-Pflicht
- [ ] 🔴 `[NF][B]` Nur lokales Modell für patienten-/praxisnahe Daten
- [ ] 🔴 `[NF][B]` Audit-Trail (10 Jahre)
- [ ] 🟡 `[NF][B]` Versionierung Fachinformationen
- [ ] 🟡 `[NF][B]` HWG-Superlativ-Filter
- [ ] 🟡 `[NF][B]` EU-AI-Act High-Risk-Klassifizierung prüfen

---

## ⚕️ Arztpraxis / MVZ
- [ ] 🔴 `[F][B]` Anamnese-Strukturierung (lokal)
- [ ] 🔴 `[F][B]` Arztbrief-Generator
- [ ] 🔴 `[F][B]` GOÄ-/EBM-Ziffern
- [ ] 🟡 `[F][B]` ICD-10-Suche
- [ ] 🔴 `[NF][B]` Nur Ollama, keine Cloud
- [ ] 🔴 `[NF][B]` Lokale Datenhaltung

## ⚖️ Anwaltskanzlei
- [ ] 🔴 `[F][B]` Mandantenakten-Suche
- [ ] 🔴 `[F][B]` Vertragsentwurf
- [ ] 🟡 `[F][B]` Rechtsprechungs-Recherche
- [ ] 🔴 `[NF][B]` Mandant-Mandant-Trennung
- [ ] 🔴 `[NF][B]` Disclaimer "Kein anwaltlicher Rat"

## 📊 Steuerberatung
- [ ] 🔴 `[F][B]` DATEV-Buchungssatz-Vorschlag
- [ ] 🟡 `[F][B]` USt-Behandlungs-Check
- [ ] 🟡 `[F][B]` BMF-Schreiben-RAG
- [ ] 🔴 `[NF][B]` GoBD-konforme Archivierung
- [ ] 🔴 `[NF][B]` Disclaimer "Keine steuerliche Beratung"

## 🔧 Handwerk / KMU
- [ ] 🟡 `[F][B]` Angebotserstellung
- [ ] 🟡 `[F][B]` Rechnung mit § 14 UStG-Pflichtangaben
- [ ] 🟢 `[F][B]` Email-Vorlagen
- [ ] 🟢 `[F][B]` Material-Kalkulation
- [ ] 🟡 `[NF][B]` Mehrfach-Mandantenfähigkeit

---

## 💡 Wishlist

- Voice-Input (Whisper)
- Slack-/MS-Teams-Integration
- Confluence / SharePoint / Notion-Anbindung
- Multi-Tenant
- Mehrsprachigkeit (EN, FR)
- Passwort-Reset per E-Mail
- 2-Faktor-Authentifizierung
- Konversations-Persistenz über Browser-Reload hinaus
- **GitHub-Strategie umsetzen** (siehe `docs/github-strategie/` — 6 Pinned Repos
  als Beratungs-Portfolio, mit `corporate-llm-platform` als Showcase)
