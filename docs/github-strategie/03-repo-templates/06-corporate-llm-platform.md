# 🤖 Corporate LLM Platform

> **Eine DSGVO/EU AI Act-konforme KI-Plattform für den deutschen Mittelstand.**
> Built and maintained by [Sascha Kern](https://github.com/<user>) —
> als lebendiger Beweis, dass KI-Strategie und KI-Umsetzung in einer Hand
> möglich sind.

![Tests](https://img.shields.io/badge/tests-88%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-active%20development-orange)

---

## 🎯 Was diese Plattform ist

Eine produktiv lauffähige LLM-Plattform für den Mittelstand, die zeigt,
wie man **KI sicher einführt** — nicht in PowerPoint, sondern als echte Software.

| Eigenschaft | Was das heißt |
|---|---|
| 🇪🇺 **EU-First** | Anthropic EU-Region konfigurierbar, lokale Modelle via Ollama |
| 🔒 **Datenschutz by Design** | Sensible Daten können vollständig lokal bleiben |
| 📚 **RAG mit Quellen-Pflicht** | EU AI Act Art. 13 — Antworten mit nachvollziehbaren Quellen |
| 🧪 **Branchen-Plugins** | z.B. Pharma mit HWG/AMG-Compliance-Prompts |
| 👥 **Rollen + Audit** | 4 Rollen, Token-Logging, DSGVO Art. 30 vorbereitet |
| 🌐 **Multi-LLM** | Cloud (Claude) und lokal (Ollama) parallel |

> **Keine PowerPoint-Plattform.** Echte Software, die Sie selbst hosten können.

---

## 🏗️ Architektur

```mermaid
graph TB
    User[👤 User] --> Streamlit[Streamlit Frontend<br/>Port 8501]
    Streamlit --> FastAPI[FastAPI Backend<br/>Port 8000]
    FastAPI --> Auth[JWT Auth<br/>4 Rollen]
    FastAPI --> Branch{Branchen-Plugin<br/>Selector}
    Branch -->|generic| Generic[Generic-Prompt]
    Branch -->|pharma| Pharma[Pharma-Plugin<br/>HWG/AMG]
    FastAPI --> Router{LLM-Router}
    Router -->|claude-*| Anthropic[☁️ Anthropic API<br/>EU-Region]
    Router -->|qwen,llama,...| Ollama[💻 Ollama lokal<br/>localhost:11434]
    FastAPI --> RAG[RAG-Service]
    RAG --> Chroma[(ChromaDB<br/>Embeddings)]
    FastAPI --> SQLite[(SQLite<br/>User, Tokens, Docs)]

    style Anthropic fill:#e1f5fe
    style Ollama fill:#fff9c4
    style Pharma fill:#fce4ec
    style FastAPI fill:#e8f5e9
```

**Analogie:** Wie eine Telefonzentrale — der Router schaltet je nach Anfrage
auf das passende "Gespräch": externer Cloud-Anschluss (Claude) oder interner
Hausanschluss (Ollama). Bei vertraulichen Themen bleibt das Gespräch im Haus.

---

## 🚀 Quick Start

### Voraussetzungen
- macOS / Linux (Windows mit WSL2)
- Python 3.12+
- [Ollama](https://ollama.com/download) (für lokale Modelle, optional)

### In 5 Minuten

```bash
git clone https://github.com/<user>/corporate-llm-platform.git
cd corporate-llm-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env editieren: ANTHROPIC_API_KEY, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD

# Terminal 1
uvicorn app.main:app --reload

# Terminal 2
streamlit run streamlit_app/app.py

# Optional Terminal 3 für lokale Modelle:
ollama serve
ollama pull qwen2.5:7b
```

→ Browser: http://localhost:8501

---

## 📚 Dokumentation

| Was | Wo |
|---|---|
| **Architektur-Übersicht** | [`docs/architecture.md`](docs/architecture.md) |
| **Phasen-Doku (von 0 bis aktuell)** | [`docs/phase-*.md`](docs/) |
| **Branchen-Plugin-Konzept** | [`docs/branchen-architektur.md`](docs/branchen-architektur.md) |
| **BFSG / Accessibility** | [`docs/quick-wins-bfsg-cloud.md`](docs/) |
| **Backlog (MoSCoW + INVEST)** | [`BACKLOG.md`](BACKLOG.md) |

---

## 🗺️ Roadmap (Auszug)

```mermaid
gantt
    title Roadmap (vereinfacht)
    dateFormat YYYY-MM-DD
    section Done
    Phase 0–2: Fundament + Auth   :done, 2026-04-01, 30d
    Phase 3: RAG + UX-Polish      :done, 2026-05-01, 30d
    Phase 4: Multi-LLM mit Ollama :done, 2026-05-25, 14d
    section In Progress
    Phase 5: Admin-Dashboard      :active, 2026-06-15, 21d
    section Planned
    Phase 6: EU-Deployment        :2026-07-15, 30d
    Phase 7: Audio/Video-Pipeline :2026-08-15, 30d
```

Vollständige Liste siehe [`BACKLOG.md`](BACKLOG.md).

---

## 🎓 Lessons Learned

Aus über 30 Phasen-Iterationen extrahiert — hier die strategisch wertvollsten:

1. **Provider-Abstraktion zahlt sich aus.** Erst Anthropic, dann Ollama — ohne
   den `BaseLLMClient` aus Phase 1 wäre Phase 4 ein Rewrite gewesen.

2. **Compliance ist kein Feature, sondern Architektur.** DSGVO/AI-Act-konforme
   Quellenangaben mussten im Daten-Modell sein, nicht im Frontend.

3. **Lokale Modelle ändern das Verkaufsgespräch.** *"Patientendaten verlassen
   nie das Haus"* ist ein anderer Pitch als "wir vertrauen auf US-Cloud-SOC2".

4. **Doku ist Verkauf.** `BACKLOG.md` zeigt strategisches Denken; `docs/phase-*`
   zeigen Arbeitsweise. Recruiter und Berater-Kollegen lesen das genau.

5. **Streaming-UX schlägt Polling.** Phasen-Status während Upload macht den
   Unterschied zwischen *"keine Ahnung wie lange"* und *"weiß was passiert"*.

---

## 🛡️ Security & Compliance

- ✅ **Keine echten API-Keys** im Repo — alles via `.env.example`
- ✅ **`data/` ist .gitignored** — Uploads, DB, Embeddings bleiben lokal
- ✅ **JWT mit konfigurierbarem Secret** — Production-Validation in `config.py`
- ✅ **Streamlit-Telemetrie deaktiviert** — kein Daten-Leak an Drittsysteme
- ✅ **Quellen-Pflicht in RAG** — EU AI Act Art. 13 Transparenz-Anforderung

Siehe auch [`SECURITY.md`](SECURITY.md) für Verantwortungsoffenlegung.

---

## 🤝 Beratung & Kontakt

Wenn dein Unternehmen vor einer ähnlichen Entscheidung steht — KI einführen,
Cloud-Strategie definieren, Compliance-Architektur aufsetzen — gerne ein
unverbindliches Gespräch:

📧 sascha.kern@nobelimpressions.com
🔗 [LinkedIn-Link einfügen]

> **Wichtig:** Dieses Repository ist **eine Referenz**, kein Produkt.
> Für eine produktive Einführung in Ihrem Unternehmen ist immer eine
> individuelle Architektur- und Compliance-Begleitung notwendig.

---

## 📄 Lizenz

[MIT](LICENSE) — kostenlos nutzbar, einschließlich kommerzielle Nutzung,
ohne Gewährleistung.
