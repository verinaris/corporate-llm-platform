# 📦 Update-Pack: Phase 3b — RAG im Chat

**9 Dateien** — Backend + Frontend Updates. **Keine neuen Dependencies** —
alles nutzt was Phase 3a bereits installiert hat.

## Was ist neu

### Backend
- `app/schemas.py` (ersetzen) — neue Felder `collection`, `top_k`, `sources`
- `app/api/chat.py` (ersetzen) — RAG-Pfad integriert
- `app/services/rag.py` (neu) — Kontext-Builder + Helper

### Frontend
- `streamlit_app/app.py` (ersetzen) — Sammlungs-Selector, Navigation
- `streamlit_app/api_client.py` (ersetzen) — Documents/RAG-Methoden
- `streamlit_app/views/chat_page.py` (ersetzen) — Quellen-Cards
- `streamlit_app/views/documents_page.py` (neu) — Upload-UI

### Tests + Doku
- `tests/test_rag.py` (neu) — 8 Tests
- `docs/phase-3b-rag-chat.md`

---

## Einbau in 4 Schritten

### 1. Beide Server stoppen
`Ctrl + C` in Terminal 1 und 2.

### 2. Update-Pack kopieren

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/update-pack-3b/* .
```

### 3. Tests laufen lassen

```bash
source .venv/bin/activate
pytest tests/ -v
```

Erwartet: **alle bisherigen Tests grün + 8 neue für RAG**.

### 4. Beide Server neu starten

```bash
# Terminal 1
uvicorn app.main:app --reload

# Terminal 2
streamlit run streamlit_app/app.py
```

Im Browser: **Hard-Reload mit `Cmd+Shift+R`**.

---

## Der WOW-Test

### Stufe 1 — Upload via UI (statt Swagger!)

1. In Streamlit eingeloggt → Sidebar: **📚 Wissensbibliothek**
2. Tab "⬆️ Upload"
3. Sammlungs-Name: `test-sammlung`
4. PDF auswählen → "📤 Hochladen"
5. ✅ Erfolgsmeldung mit Chunk-Count

### Stufe 2 — RAG aktivieren

1. Sidebar: **Sammlung-Dropdown** unter "📚 Wissensbibliothek"
2. `test-sammlung` wählen
3. **Wechsel auf 💬 Chat** → oben siehst du das Banner **"📚 RAG aktiv"**

### Stufe 3 — Magie erleben

Stelle eine Frage zum PDF-Inhalt. Die Antwort kommt mit:
- 🤖 Antwort, die deine PDF zitiert
- 📚 **Aufklappbarer Quellen-Bereich** mit Filename, Seite, Relevanz-Score
- 💰 Tokens & Kosten wie immer

### Stufe 4 — A/B-Vergleich

1. **Mit RAG:** Frag etwas Spezifisches aus deinem PDF → präzise Antwort + Quellen
2. **Ohne RAG:** Sammlung auf "— keine —" → Claude antwortet aus Allgemeinwissen → keine Quellen

→ Du erlebst direkt, warum RAG der Game-Changer für Corporate-Nutzung ist.

### Stufe 5 — Pharma-User mit RAG (für die ganz Mutigen)

1. Mit Pharma-User einloggen (`pharma@nobelimpressions.com`)
2. Sammlung wählen
3. Frage stellen
4. Antwort hat:
   - **HWG-konforme Formulierungen** (vom Pharma-Plugin)
   - **Quellenangaben** aus deinem Dokument (vom RAG)
   - **Compliance-Hinweis** am Ende

Drei Sicherheitsnetze auf einmal. 🎯

---

## Falls etwas hakt

### "Sammlung nicht gefunden"
→ Hast du tatsächlich ein PDF hochgeladen? Erst Upload via UI/Swagger, dann RAG.

### Quellen-Cards leer
→ Möglich, dass die Frage zu unspezifisch ist. ChromaDB findet trotzdem die "ähnlichsten" Chunks, aber sie sind dann nicht relevant. Versuch eine konkretere Frage.

### "Backend nicht erreichbar"
→ Läuft uvicorn? Terminal 1 checken.

### Streamlit zeigt alte Sidebar
→ Browser-Hard-Reload (`Cmd+Shift+R`)

---

## Git-Commit

```bash
git add .
git commit -m "Phase 3b: RAG im Chat (Sammlungs-Selector, Quellen-Cards, Upload-UI)"
git push
```

---

## Was du jetzt hast

- ✅ Vollständiger RAG-Workflow End-to-End
- ✅ Upload direkt aus Streamlit (kein Swagger nötig)
- ✅ Sammlungsverwaltung mit Cards + Stats
- ✅ Quellen-Transparenz (EU AI Act Art. 13!)
- ✅ Funktioniert auch mit Pharma-Branche kombiniert
- ✅ Granulare Rechte: Admin/Compliance dürfen verwalten, User dürfen lesen

## Was als nächstes (Phase 3c, optional)

- Pharma-spezifische Sammlungen mit Pflicht-Quellen
- PDF-Vorschau direkt in der Quellen-Card
- Sammlung-Beschreibungen + Tags
- Versionierung von Dokumenten
