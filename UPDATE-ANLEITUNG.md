# 🔧 KOMPLETT-PACK: Duplikatsprüfung (konsolidiert)

Dieses Pack ersetzt die beiden vorherigen (`hotfix-dedupe` + `hotfix-backfill`)
durch eine **konsistente, in sich geschlossene Lösung**.

## Was drin ist

| Datei | Was es macht |
|-------|--------------|
| `app/models.py` | `Document.content_hash` Feld + DocumentCollection |
| `app/database.py` | Migration + Backfill (defensiv, kein Hard-Crash) |
| `app/api/documents.py` | Hash-Check vor Upload + Streaming-Variante |
| `streamlit_app/views/documents_page.py` | ⚠️-Anzeige bei Duplikaten |
| `tests/test_documents.py` | Tests inkl. 4 für Duplikatsprüfung |

## Einbau (sauber)

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform

# Cache leeren — sonst nimmt Python evtl. alte .pyc Dateien
find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} +

# Komplett-Pack drüber kopieren
cp -R /Pfad/zu/komplett-dedupe/* .

# Beide Server neu starten
# Terminal 1 (Backend): Ctrl+C + Pfeil↑ Enter
# Terminal 2 (Streamlit): Ctrl+C + Pfeil↑ Enter
```

## Was beim ersten Start passiert

In der **Backend-Konsole** solltest du sehen:

```
[Migration] documents.content_hash hinzugefügt    ← falls Spalte noch fehlt
[Migration] X bestehende Dokument(e) nachträglich gehashed
```

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
# → 88 passed, 1 skipped
```

## Was sich an der Logik geändert hat

Der Backfill ist jetzt **robuster**:
- Wenn das Modell-Feld fehlt → Skip + Log (statt Crash)
- Wenn Files auf Disk fehlen → Skip + Log
- Jeder unerwartete Fehler → wird gefangen, Server startet trotzdem

## Test in der UI

1. Beliebige PDF in Sammlung A → ✅ Upload klappt
2. **Genau dieselbe PDF** in Sammlung A → ⚠️ Warnung mit Datum + Uploader
3. Dieselbe PDF in Sammlung B → ✅ klappt (andere Sammlung)
4. PDF umbenennen + in A → ⚠️ erkannt (Hash entscheidet)

## Falls trotzdem was schief geht

Schick mir die **gesamte Backend-Konsolen-Ausgabe** vom Start (von "INFO: Will watch for changes..." bis "ERROR" oder erfolgreichem Start) — dann sehe ich genau was anders ist.
