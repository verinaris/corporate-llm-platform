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
## 📋 Phase 3c — Document-Storage UX-Verbesserungen
Funktional

 🟡 [F] Upload-Fortschrittsanzeige in % während des Hochladens

Damit User abschätzen kann, wie lange es noch dauert
Implementierungs-Optionen siehe docs/phase-3c-upload-progress.md (kommt)


 🟡 [F] Phasen-Statusmeldung nach Upload-Abschluss:
"Hochladen → PDF lesen → Chunks erstellen → Embeddings → Fertig"
 🟢 [F] PDF-Vorschau direkt in der Quellen-Card im Chat
 🟢 [F] Sammlung-Beschreibungen + Tags
 🟢 [F] Versionierung von Dokumenten (alte Version archivieren bei Re-Upload)

Nichtfunktional

 🟡 [NF] Server-Sent Events (SSE) für Echtzeit-Progress (Backend)
 🟢 [NF] Background-Job-Queue (z.B. mit RQ oder Celery)
für Uploads > 100 MB, damit Browser nicht blockiert

---

## 📋 Phase 4 — Multi-LLM-Routing

- [ ] 🔴 `[F]` Ollama-Adapter (lokales Modell)
- [ ] 🟡 `[F]` OpenAI-Adapter
- [ ] 🟡 `[F]` Regel-Router (sensible Daten → Ollama)
- [ ] 🟢 `[F]` Fallback-Logik

---

## 📋 Phase 5 — Admin-Dashboard

- [ ] 🟡 `[F]` Token-/Kosten-Charts
- [ ] 🟡 `[F]` CSV-/Excel-Export
- [ ] 🔴 `[F]` Daten-Lösch-Funktion (DSGVO Art. 17)
- [ ] 🔴 `[F]` Audit-Log-Ansicht
- [ ] 🟡 `[F]` User-Verwaltung im Frontend

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
