# Phase 3c — Document-Storage UX-Verbesserungen

**Ziel:** Politur der Wissensbibliothek. Was bisher technisch funktionierte,
wird **transparent** und **kontrollierbar** für den User.

## Was neu ist

### 1️⃣ Upload-Phasen-Status (Live)

Bisher: Spinner dreht sich, niemand weiß wie weit der Upload ist.
Jetzt: **Live-Status-Updates** während des Uploads:

```
✅ 1️⃣  Datei wird empfangen — Datei empfangen (15.3 MB)
✅ 2️⃣  PDF wird gelesen — 47 Seiten (1.2s)
✅ 3️⃣  Chunks werden erstellt — 128 Stück
⏳ 4️⃣  Embeddings werden generiert — Erstelle Embeddings für 128 Chunks…
✅ 4️⃣  Embeddings werden generiert — fertig (8.7s)
✅ 5️⃣  Indexierung abgeschlossen
```

**Technik:** Backend-Endpoint `POST /documents/stream` sendet NDJSON
(Newline-Delimited JSON). Streamlit liest Zeile für Zeile und aktualisiert
einen `st.status()`-Container live.

> Eine echte byte-genaue % wäre nur mit Async-Job-Queue möglich (Phase 6+).
> Diese Phasen-Lösung ist der pragmatische Sweet-Spot.

### 2️⃣ Sammlungs-Beschreibungen + Tags

**Neue DB-Tabelle** `document_collections` mit:
- `description` (max 2000 Zeichen)
- `tags` (komma-separiert)
- `created_by`, `created_at`, `updated_at`

**UI-Integration:**
- Beim Upload in **neue** Sammlung: Beschreibung erfassbar
- In Sammlungs-Card: Beschreibung + Tags sichtbar
- ✏️-Expander zum nachträglichen Bearbeiten (nur Admin/Compliance)

**API-Endpoints (neu):**
- `POST /documents/collections` — anlegen mit Beschreibung + Tags
- `PUT /documents/collections/{name}` — Beschreibung/Tags ändern
- `GET /documents/collections/{name}` — Info abrufen
- `GET /documents/collections` — jetzt mit `description`/`tags` in Response

### 3️⃣ Quellen-Cards erweitert

Im Chat zeigen die Quellen-Cards jetzt:

| Bisher | Jetzt |
|--------|-------|
| 200-Zeichen-Auszug | + **📖 Mehr Kontext** Toggle → voller Chunk-Text |
| Keine PDF-Verbindung | + **📥 PDF holen** → Download-Button erscheint |
| Filename, Seite, Relevanz | + Vollständiger Kontext im Textarea |

**Technik:**
- `SourceReference.full_text` (neu) liefert kompletten Chunk
- `GET /documents/{id}/file` (neu) liefert Original-PDF (mit Bearer-Auth)
- Streamlit cached PDFs in Session-State, damit pro Quelle nur 1x geholt

### 4️⃣ Git-Aufräum-Hilfe

- `data/README.md` erklärt warum `data/` gitignored ist
- `.gitignore` mit Ausnahme für `data/README.md`

## Was Phase 3c NICHT bringt

- ❌ Echte byte-% (würde Async-Job-Queue brauchen — Phase 6+)
- ❌ Inline-PDF-Viewer (Streamlit kann's nicht nativ; PDFs öffnen im neuen Tab/Download)
- ❌ Multi-Format-Upload (`.docx`, `.txt` etc.) — eigene Phase 3d
- ❌ Versionierung bei Re-Upload — verschoben

## Architektur

```
┌─────────────────────┐    POST /documents/stream
│  Streamlit          │ ───────────────────────────► ┌───────────────┐
│  (Phasen-UI)        │ ◄─── NDJSON-Stream ───────── │  FastAPI      │
│                     │     {phase, status, ...}     │  Backend      │
└─────────────────────┘                              │               │
                                                     │  ─────────    │
        Phase-Updates                                │  pypdf        │
        kommen live an                               │  chunker      │
        und triggern                                 │  ChromaDB     │
        UI-Render                                    └───────────────┘
```

**Analogie:** Bisher Postpaket — du wirfst ein, es kommt irgendwann an.
Jetzt: Sendungsverfolgung mit Stationen ("Frankfurt → Köln → Zustellung").

## Test

```bash
pytest tests/test_documents.py -v
# → 18 grüne (12 alte + 6 neue für Collections + Download)
```

## Migration

Beim ersten Start nach dem Update legt SQLModel die neue
`document_collections`-Tabelle automatisch an. **Keine manuelle Migration nötig.**

Existierende Sammlungen ohne Metadaten erscheinen weiter in der Liste — nur
ohne Beschreibung/Tags. Beim ersten Edit speichert das System die Metadaten.
