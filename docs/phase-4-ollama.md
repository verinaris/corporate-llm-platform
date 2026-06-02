# Phase 4 — Multi-LLM mit Ollama (lokale Modelle)

**Ziel:** Die Provider-Abstraktion aus Phase 1 ausspielen — User können zwischen
Cloud-Modellen (Claude) und **lokalen Modellen** (Ollama) wählen.

**Der USP der Plattform:** Sensible Daten (Patientendaten, Mandantenakten,
Steuerbelege) können mit lokalen Modellen verarbeitet werden, **ohne dass je
ein Byte den Mac verlässt**.

## Architektur

```
                      ┌──────────────────────┐
        User wählt    │  Streamlit-Sidebar   │
        Modell  ───►  │  🤖 Modell-Dropdown   │
                      │   ☁️ Claude (Cloud)   │
                      │   💻 qwen2.5:7b      │
                      │   💻 llama3.2:3b     │
                      └──────────────────────┘
                                │
                                ▼
                      ┌──────────────────────┐
                      │  FastAPI /chat       │
                      │  _resolve_client()   │
                      └──────────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  ▼                           ▼
        ┌─────────────────┐         ┌────────────────────┐
        │ AnthropicClient │         │  OllamaClient       │
        │ (Cloud)         │         │ (localhost:11434)   │
        └─────────────────┘         └────────────────────┘
                  │                           │
                  ▼                           ▼
        api.anthropic.com            ollama serve (lokal)
        💰 kostet Geld               💰 0$ pro Token
        🌐 braucht Internet          📡 100% offline-fähig
        🚀 sehr leistungsfähig       💻 begrenzt durch eigene Hardware
```

**Analogie:** Du hattest bislang einen Lieferdienst (Claude/Anthropic).
Phase 4 macht draus eine Logistik-Plattform: je nach Sendung wählst du
Express-Cloud-Versand (teuer, schnell, online) oder Eigenfuhrwerk (gratis,
sicher, offline).

## Was neu ist

| Komponente | Aufgabe |
|------------|---------|
| `app/llm/ollama_client.py` | NEU — implementiert `BaseLLMClient` für Ollama |
| `app/api/models.py` | NEU — Endpoint `/models/available` listet alle nutzbaren Modelle |
| `app/api/chat.py` | Resolver wählt Anthropic vs. Ollama anhand des Modell-Namens |
| `app/pricing.py` | Erweitert: lokale Modelle = 0$ |
| `streamlit_app/app.py` | Modell-Dropdown wird dynamisch vom Backend befüllt |
| `streamlit_app/api_client.py` | NEU — `list_available_models()` Methode |

## Konfiguration

In der `.env`:
```bash
OLLAMA_BASE_URL=http://localhost:11434   # Default — Ollama läuft lokal
```

Bei Remote-Ollama (z.B. auf einem Server im LAN):
```bash
OLLAMA_BASE_URL=http://192.168.1.42:11434
```

## Ollama-Setup (User-Schritt)

```bash
# 1. Ollama installieren (einmalig)
brew install ollama

# 2. Server starten (in eigenem Terminal)
ollama serve

# 3. Ein Modell ziehen (einmalig pro Modell)
ollama pull qwen2.5:7b
# Weitere Optionen:
ollama pull llama3.2:3b    # klein, schnell (2 GB)
ollama pull llama3.1:8b    # mittel (4.7 GB)
ollama pull mistral:7b     # mittel (4.1 GB)
```

Welche Modelle installiert sind, prüfst du mit `ollama list`.

## Wie wählt der Resolver?

Im Backend (`app/api/chat.py`):

```python
def _resolve_client(model: str) -> BaseLLMClient:
    if model.startswith("claude-"):
        return AnthropicClient()
    if ":" in model or model.lower().startswith((
        "llama", "qwen", "mistral", "phi", "gemma", ...
    )):
        return OllamaClient()
    raise HTTPException(400, detail="Unbekanntes Modell...")
```

**Heuristik:**
- `claude-*` → Anthropic-Cloud
- `name:tag` (z.B. `qwen2.5:7b`) → Ollama
- Bekannte Open-Source-Modell-Familien (llama, qwen, mistral...) → Ollama
- Alles andere → 400 Fehler mit Hinweis

## Frontend-Verhalten

1. Beim Login fragt Streamlit `GET /models/available` ab
2. Backend liefert alle verfügbaren Modelle pro Provider, mit Label und `is_local`-Flag
3. Streamlit baut das Dropdown dynamisch:
   ```
   Haiku 4.5  ·  schnell & günstig
   Sonnet 4.6  ·  ausgewogen (Default)
   Opus 4.7  ·  stärkstes Modell
   qwen2.5:7b  ·  lokal (4.4 GB)
   llama3.2:3b  ·  lokal (2.0 GB)
   ```
4. Bei Auswahl eines lokalen Modells erscheint unter dem Selector:
   *"💻 Lokales Modell — keine Daten verlassen deinen Mac"*

## Wer kann was?

| Feature | Cloud (Claude) | Lokal (Ollama) |
|---------|----------------|----------------|
| Chat | ✅ | ✅ |
| RAG (Sammlungen) | ✅ | ✅ — Embeddings sind sowieso lokal |
| Pharma-Plugin | ✅ | ✅ — HWG/AMG-Prompt funktioniert mit beiden |
| Streaming-Response | ⏸️ noch nicht | ⏸️ noch nicht |
| Kosten pro Request | $0.003–$0.30 | **$0.00** |

## Bekannte Einschränkungen

- **Erste Anfrage langsam**: Ollama lädt das Modell beim ersten `chat`-Call in den RAM. Kann 10-30s dauern. Danach ist's flott.
- **Qualität**: 7B-Modelle sind nicht auf Claude-Niveau. Bei einfachen Fragen / RAG-Tasks aber sehr gut nutzbar.
- **Hardware-Limit**: Auf einem 8 GB Mac läuft sinnvoll nur Modelle bis ~7B. Für 13B+ Modelle: 16+ GB RAM nötig.

## Tests

```bash
pytest tests/test_ollama.py tests/test_pricing.py tests/test_models_endpoint.py -v
# → 32 neue grüne Tests
pytest tests/ -v
# → 84 passed, 1 skipped
```

## Was Phase 4 NICHT macht

- ❌ **Regel-Router** (Phase 4c): *"Wenn der User Pharma + Patientendaten → automatisch lokal"*
  Kommt später, wenn ein PII-Detektor steht (Phase 3+ TODO im Backlog).
- ❌ **Streaming-Responses**: Antwort kommt komplett am Ende, nicht wortweise.
- ❌ **Modell-Vergleichs-Modus**: Frage parallel an Claude + Qwen — wird in Phase 5+ interessant.
- ❌ **OpenAI-Adapter**: Wäre analog zu OllamaClient leicht, machen wir bei Bedarf.

## Nächste Sinnvolle Schritte

| Phase | Was |
|-------|-----|
| **4c** | PII-Filter + Regel-Router (sensible Daten → automatisch lokal) |
| **5** | Admin-Dashboard mit Provider-Auswertung (welcher Provider wurde wann genutzt?) |
| **6** | Cloud-Deployment (Hetzner mit Ollama im Container?) |
