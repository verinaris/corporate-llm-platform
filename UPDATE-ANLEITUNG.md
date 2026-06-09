# 🔧 Hotfix: DSGVO-Löschen Bestätigung im GitHub-Stil

## Was war das Problem

Die Bestätigungs-Phrase war `LOSCHEN <id>` (ohne Umlaut) — intuitiv tippt
man aber `LÖSCHEN`. String-Vergleich war strikt → Button blieb deaktiviert.

## Was der Fix macht

Bestätigung jetzt: **`DELETE USER <id>`** (GitHub-Stil, international, unverwechselbar).
Außerdem: Groß-/Kleinschreibung wird ignoriert (`delete user 3` funktioniert auch).

## Einbau

```bash
cd /Volumes/Data2/Claude-Code/corporate-llm-platform
cp -R /Pfad/zu/hotfix-delete-confirm/* .
```

**Streamlit aktualisiert sich automatisch** (Hot-Reload), sonst Cmd+Shift+R.

## Verifikation

1. Sidebar → 🛡️ Admin / Compliance
2. Tab 🗑 DSGVO Art. 17 — Löschen
3. User-ID: `3`
4. Bestätigung tippen: `DELETE USER 3` (oder `delete user 3` — egal)
5. Button wird aktiv → Löschung läuft
