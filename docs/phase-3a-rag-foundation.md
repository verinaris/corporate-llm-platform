# Phase 3a — Document-Storage + Embeddings

**Ziel:** Fundament für RAG. PDF-Dateien werden hochgeladen, in Stücke
zerlegt, embedded, und in einer lokalen Vektor-Datenbank gespeichert.

## Architektur

```
PDF-Upload
   │
   ▼  pypdf
Text pro Seite
   │
   ▼  chunker (800 Zeichen, 120 Overlap)
Chunks mit Metadaten (Seite, Reihenfolge)
   │
   ▼  ChromaDB (eingebautes Embedding-Modell)
Vektoren in ./data/chroma/
   │
   ▼
Such-Endpoint /documents/search → liefert ähnliche Chunks
```

**Analogie:** Wie ein Verlagslektor, der ein Buch in beschriftete Karteikarten
zerlegt und in einem Regal nach Themen sortiert ablegt. Wenn jemand nach
einem Thema fragt, zieht das System die passenden Karteikarten heraus.

## Komponenten

| Datei | Aufgabe |
|-------|---------|
| `app/services/document_store.py` | ChromaDB-Wrapper (Persistenz, Add, Query, Delete) |
| `app/services/document_processor.py` | PDF → Text → Chunks |
| `app/models.py` (Document) | Metadaten in SQLite (Größe, Seiten, Uploader) |
| `app/schemas_documents.py` | Pydantic-Modelle für die API |
| `app/api/documents.py` | REST-Endpoints |
| `app/auth/dependencies.py` | Neue Dependency `require_admin_or_compliance` |

## Speicher-Layout

```
data/
├── platform.db                  ← Metadaten (SQLite)
├── chroma/                      ← Vektor-DB (ChromaDB)
│   ├── chroma.sqlite3
│   └── <collection-uuids>/
└── documents/                   ← Original-PDFs
    ├── 3f8b9...pdf
    └── 4a2c1...pdf
```

> **Wichtig:** Die Original-PDFs werden auf der Platte abgelegt, nicht in
> ChromaDB. So bleibt die Vektor-DB schlank.

## API-Endpoints

| Methode | Pfad | Rolle | Zweck |
|---------|------|-------|-------|
| POST | `/documents` | Admin, Compliance | PDF hochladen |
| GET | `/documents` | alle | Dokumente listen |
| GET | `/documents/{id}` | alle | Einzelnes Dokument |
| DELETE | `/documents/{id}` | Admin, Compliance | Löschen (DB+Vektor+Datei) |
| GET | `/documents/collections` | alle | Sammlungen + Stats |
| GET | `/documents/search` | alle | Vektor-Suche (Test-Endpoint) |

## Sammlungs-Modell

Sammlungen sind **frei benannte Container**. Konvention:

| Sammlungs-Name | Beispiel-Inhalt |
|----------------|-----------------|
| `pharma-fachinfos` | Fachinformationen pharmazeutischer Präparate |
| `pharma-leitlinien` | AWMF-Leitlinien |
| `hr-handbuch` | Personalhandbuch |
| `tech-doku` | Interne technische Dokumentation |

**Regeln für Namen** (ChromaDB-Vorgabe):
- 3-64 Zeichen
- Nur Kleinbuchstaben, Ziffern, `-` oder `_`
- Muss mit Buchstabe/Ziffer beginnen und enden

## Erste Tests

### 1. Sammlung anlegen (passiert implizit beim ersten Upload)

```bash
# Über Swagger:
# POST /documents mit Form-Daten:
#   collection = "pharma-fachinfos"
#   file = <eine PDF deiner Wahl>
```

### 2. Liste prüfen

```bash
# GET /documents
# → liefert die hochgeladenen Dokumente mit Chunk-Count
```

### 3. Suche testen

```bash
# GET /documents/search?q=Wechselwirkungen&collection=pharma-fachinfos&limit=3
# → liefert die 3 ähnlichsten Chunks samt Seite + Distance
```

## Erst-Aufruf — was passiert

Beim **allerersten** Upload lädt ChromaDB sein Default-Embedding-Modell
herunter (~80 MB, all-MiniLM-L6-v2). Das dauert **1-3 Minuten**. Danach
ist alles blitzschnell.

Du erkennst das Laden im Backend-Log an Zeilen wie:
```
Downloading model.onnx: 80.5MB/80.5MB
```

## Was Phase 3a NICHT macht

- ❌ OCR für gescannte PDFs (kommt mit `pytesseract` in Phase 3+)
- ❌ Word/Excel/HTML zusätzlich zu PDF
- ❌ RAG-Integration im /chat-Endpoint (kommt in **Phase 3b**)
- ❌ Streamlit-Upload-UI (kommt in 3b)
- ❌ Granulare Zugriffsrechte pro Sammlung (Phase 5)

## Tests laufen lassen

```bash
# Schnell-Tests (ohne ChromaDB-Roundtrip):
pytest tests/test_documents.py -v

# Inklusive ChromaDB (dauert beim ersten Mal ~2 Min):
ENABLE_CHROMA_TESTS=1 pytest tests/test_documents.py -v
```

## Was kommt als nächstes

**Phase 3b:** Im Chat-Endpoint wird optional ein `collection`-Parameter
akzeptiert. Wenn gesetzt:
1. Frage wird embedded
2. Top-N relevante Chunks aus ChromaDB werden gefunden
3. Diese werden als Kontext an Claude geschickt
4. Antwort enthält Quellenangaben (Dateiname + Seite)
5. Streamlit-UI bekommt Sammlungs-Selektor + Upload-Button für Admins
