# Phase 3b — RAG im Chat

**Ziel:** RAG-Fundament aus Phase 3a wird im Chat sichtbar. User wählt
eine Sammlung, stellt eine Frage — Claude antwortet aus den hochgeladenen
Dokumenten und nennt die Quellen.

## Architektur

```
Streamlit-Sidebar
  └─ Sammlung wählen ("test-sammlung")
        ▼
Chat-Page → User-Frage
        ▼
POST /chat  { "messages": [...], "collection": "test-sammlung" }
        ▼
Backend:
  1. Letzte User-Frage extrahieren
  2. Vektor-Suche in ChromaDB (Top-K = 4)
  3. Chunks als Kontext-Block formatieren
  4. Kontext + RAG-Instruktion als System-Message vorne anhängen
  5. Claude-Aufruf
  6. Sources strukturiert in Response
        ▼
ChatResponse { "content": "...", "sources": [...] }
        ▼
Chat-Page rendert:
  - Antwort als Markdown
  - 📚 Expandierbare Quellen-Cards (Filename, Seite, Relevanz, Auszug)
```

## Was Phase 3b NEU bringt

| Komponente | Aufgabe |
|------------|---------|
| `app/services/rag.py` | RAG-Logik: Kontext bauen + injizieren |
| `app/schemas.py` | `SourceReference`, erweiterte `ChatRequest/Response` |
| `app/api/chat.py` | Optional `collection`-Parameter → RAG-Pfad |
| `streamlit_app/views/documents_page.py` | UI für Upload + Sammlungs-Verwaltung |
| `streamlit_app/views/chat_page.py` | Quellen-Cards unter der Antwort |
| `streamlit_app/app.py` | Sammlung-Selector in Sidebar |
| `streamlit_app/api_client.py` | Methoden für `upload_document`, `list_collections`, RAG-Chat |

## Quellen-Karte (UI)

```
📚 4 Quelle(n) verwendet (ausklappbar)
└─ 1. fachinfo.pdf · Seite 3              Relevanz: 87%
   > "Bei Wechselwirkungen mit Cumarinen…"
   ─────────────────────────────────────────
   2. leitlinie.pdf · Seite 12            Relevanz: 78%
   > "Die Tagesdosis sollte nicht überschritten werden…"
```

Relevanz wird aus der ChromaDB-Distance berechnet:
- 0.0 (identisch) → 100%
- 1.5 (irrelevant) → 0%

## Wer darf was?

| Rolle | Chat mit RAG | Sammlungen sehen | Upload | Löschen |
|-------|--------------|------------------|--------|---------|
| Admin | ✅ | ✅ | ✅ | ✅ |
| Compliance-Officer | ✅ | ✅ | ✅ | ✅ |
| Pharma-Referent | ✅ | ✅ | ❌ | ❌ |
| User | ✅ | ✅ | ❌ | ❌ |

## Test-Flow im Browser

### 1. PDF hochladen (als Admin)

- Sidebar: **📚 Wissensbibliothek**
- Tab "⬆️ Upload"
- Sammlungs-Name eingeben (z.B. `test-sammlung`)
- PDF auswählen
- Hochladen klicken

### 2. RAG aktivieren

- Sidebar: unter "📚 Wissensbibliothek" die Sammlung `test-sammlung` wählen
- Im Chat erscheint: **"📚 RAG aktiv"**-Banner

### 3. Frage stellen

- Chat: eine Frage zum PDF-Inhalt stellen
- Antwort kommt mit:
  - Spinner zeigt "sucht in `test-sammlung`..."
  - Inhalt mit eventuellen `[Quelle 1]`-Verweisen
  - Expander mit 4 Quellen-Cards

### 4. Vergleich: Mit vs ohne RAG

Stelle dieselbe Frage:
- **Mit Sammlung gewählt:** Antwort verweist auf dein PDF
- **Mit "— keine —":** Claude antwortet aus Allgemeinwissen, keine Quellen

→ Mind blowing 🤯

## Was Phase 3b nicht macht

- ❌ Quellen-PDF-Vorschau (Klick auf Quelle → Seite öffnen) — kommt in 3c
- ❌ Sammlungs-Beschreibungen / Tags — kommt in 3c
- ❌ Pharma-spezifische Pflicht-Sammlungen — kommt in 3c
- ❌ Granulare Zugriffsrechte pro Sammlung — Phase 5
- ❌ Sammlung-Versionierung — Phase 5

## Tests

```bash
pytest tests/test_rag.py -v        # 8 grüne erwartet
pytest tests/ -v                   # alle 46+ Tests
```
