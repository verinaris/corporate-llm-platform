# Architektur

## Überblick

Die Plattform ist als **mehrschichtige Anwendung** aufgebaut. Jede Schicht hat eine klar abgegrenzte Aufgabe.

```
┌────────────────────────────────────────────┐
│  Präsentation (Phase 2)                    │
│  Streamlit-UI im Browser                   │
└────────────────────┬───────────────────────┘
                     │ HTTPS/JSON
┌────────────────────▼───────────────────────┐
│  API-Gateway (Phase 1)                     │
│  FastAPI — Routing, Validation, Auth       │
└──┬─────────────┬───────────────┬───────────┘
   │             │               │
   ▼             ▼               ▼
┌────────┐  ┌──────────┐   ┌────────────┐
│Services│  │LLM-Layer │   │ Datenhal-  │
│        │  │ (Adapter)│   │  tung      │
│Token-  │  │Anthropic │   │SQLite +    │
│Tracker │  │OpenAI    │   │ChromaDB    │
│RAG     │  │Ollama    │   │            │
└────────┘  └──────────┘   └────────────┘
```

## Kernprinzipien

### 1. Provider-Agnostik
Der LLM-Layer ist hinter einer **abstrakten Basis-Klasse** (`BaseLLMClient`) versteckt. Die App kennt nur das Interface, nicht den konkreten Anbieter. Neue Provider werden in Phase 4 ohne Änderungen am Rest der App ergänzt.

**Analogie:** USB-Standard — jedes Gerät passt in jeden Port.

### 2. Datentrennung
- **Strukturierte Daten** (User, Logs, Konversationen) → SQLite
- **Unstrukturierte Daten** (Embeddings für RAG) → ChromaDB

### 3. Konfiguration über Environment
Alle veränderlichen Einstellungen kommen aus `.env`. **Keine Secrets im Code.**

### 4. Token-Logging als Querschnitt
Jeder LLM-Aufruf wird über den `TokenTracker` geloggt — egal welcher Provider, egal welcher Endpoint. Das ermöglicht später eine zentrale Kostenkontrolle.

## Datenfluss eines Chat-Requests

```
1. Client schickt POST /chat mit messages + user_id
2. FastAPI validiert JSON gegen ChatRequest-Schema
3. Resolver wählt Client anhand Modellname (claude-* → AnthropicClient)
4. Client sendet Request an Anthropic API
5. Antwort wird in einheitliche LLMResponse umgepackt
6. TokenTracker schreibt Eintrag in SQLite (input/output/cost/latency)
7. ChatResponse wird an Client zurückgegeben
```

## Sicherheitsmodell (Phase 1)

- **Aktuell:** Kein Auth — nur lokale Nutzung
- **Phase 2:** JWT-basierte Auth, Rollen (admin, user)
- **Phase 5+:** Rate Limiting, IP-Allowlisting, Audit-Log

## Skalierungspfad

Die aktuelle SQLite-Lösung trägt einige tausend Requests problemlos. Für Produktion später:

| Komponente | Lokal (jetzt) | Produktion (später) |
|------------|---------------|---------------------|
| DB | SQLite | PostgreSQL |
| Vektor-DB | ChromaDB lokal | Qdrant/Weaviate |
| Frontend | Streamlit | Next.js/React |
| Deployment | uvicorn direkt | Docker + Reverse Proxy |
