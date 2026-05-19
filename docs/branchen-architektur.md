# 🏢 Branchen-Architektur

**Status:** Plugin-Mechanik vorhanden (leeres Gerüst), Anschluss an `/chat` kommt in Phase 2.

## Idee

Eine Branche ist wie eine **Brille**, die ein User aufsetzt — sie färbt seine Eingaben und Ausgaben, ohne den Rest des Systems zu verändern.

```
User-Input
    │
    ▼
┌─────────────────────────────────┐
│   Branchen-Plugin.pre_process   │  ← z.B. PII-Filter
└─────────────────────────────────┘
    │
    ▼
   LLM (Claude)  ← bekommt ggf. Branchen-System-Prompt vorgesetzt
    │
    ▼
┌─────────────────────────────────┐
│  Branchen-Plugin.post_process   │  ← z.B. Disclaimer anhängen
└─────────────────────────────────┘
    │
    ▼
User-Antwort
```

## Was ein Plugin steuert

| Methode | Wann | Wofür |
|---------|------|-------|
| `get_system_prompt()` | vor LLM-Call | Branchen-System-Prompt setzen |
| `pre_process_messages()` | vor LLM-Call | Input filtern/validieren (PII, Verbote) |
| `post_process_response()` | nach LLM-Call | Output anreichern/filtern |
| `required_disclaimer` | jederzeit | Pflicht-Disclaimer-Text |

## Aktueller Stand

```
app/branches/
├── __init__.py       # Plugin-Registry
├── base.py           # BranchPlugin (Abstract Base Class)
├── generic/
│   └── plugin.py     # Default: kein Eingriff  ✅ aktiv
└── pharma/
    └── plugin.py     # Gerüst, Implementierung Phase 2+3  🚧
```

> **Phase 1:** Plugins sind angelegt, aber **nicht in `/chat` verkabelt**. Das passiert in Phase 2 zusammen mit User-Login (User → Branche → Plugin).

## Eine neue Branche hinzufügen — in 4 Schritten

**Beispiel:** Wir wollen `legal` (Anwaltskanzlei) ergänzen.

### 1. Ordner anlegen

```
app/branches/legal/
├── __init__.py
└── plugin.py
```

### 2. Plugin-Klasse schreiben (`legal/plugin.py`)

```python
from app.branches.base import BranchPlugin

class LegalPlugin(BranchPlugin):
    branch_code = "legal"
    display_name = "Anwaltskanzlei"

    def get_system_prompt(self):
        return (
            "Du unterstützt Rechtsanwält:innen. "
            "Du erteilst KEINEN anwaltlichen Rat. "
            "Verweise auf gesetzliche Grundlagen, "
            "aber lasse die finale Beurteilung beim Anwalt."
        )

    @property
    def required_disclaimer(self):
        return "\n\n---\nDies ist kein anwaltlicher Rat."

    def post_process_response(self, text):
        return text + (self.required_disclaimer or "")
```

### 3. In Registry eintragen (`app/branches/__init__.py`)

```python
from app.branches.legal.plugin import LegalPlugin

_REGISTRY = {
    "generic": GenericPlugin,
    "pharma": PharmaPlugin,
    "legal": LegalPlugin,   # NEU
}
```

### 4. Test ergänzen (`tests/test_branches.py`)

```python
def test_legal_plugin():
    plugin = get_plugin("legal")
    assert plugin.branch_code == "legal"
    assert "kein anwaltlicher Rat" in plugin.post_process_response("x")
```

**Fertig.** Eine Minimal-Branche braucht also ~30 Zeilen Code.

## Aufwand pro Branche (realistisch)

| Aufwandskategorie | Beispiel | Zeit |
|-------------------|----------|------|
| **Klein** | System-Prompt + Disclaimer | 1–2 Stunden |
| **Mittel** | + PII-Filter, + spezifische Validatoren | 1–2 Tage |
| **Groß** | + externe Integrationen (DATEV, juris), + High-Risk-Compliance | Wochen |

## Geplanter Anschluss in Phase 2

In Phase 2 wird im `/chat`-Endpoint folgendes ergänzt (vereinfacht):

```python
# In app/api/chat.py
from app.branches import get_plugin

@router.post("")
async def chat(request, user=Depends(current_user), ...):
    plugin = get_plugin(user.branch)         # Branche aus User-Profil

    messages = plugin.pre_process_messages(request.messages)
    if sys_prompt := plugin.get_system_prompt():
        messages = [ChatMessage(role="system", content=sys_prompt)] + messages

    result = await client.chat(messages, ...)

    result.content = plugin.post_process_response(result.content)
    return result
```

Damit ist die Mechanik **transparent eingehängt** — User der Branche `generic` merkt nichts, User der Branche `pharma` bekommt die Pharma-Brille aufgesetzt.

## Was wird *nicht* per Plugin gelöst

Manche Sachen gehören **nicht** in ein Branchen-Plugin, sondern in den Kern:

- ❌ Authentifizierung (Kern: alle Branchen brauchen Login)
- ❌ Datenbank-Schema (Kern: User, Logs)
- ❌ LLM-Adapter (Kern: Provider-Auswahl)
- ✅ Aber: Branchen können vorschreiben *"nur lokales Modell"* — das ist eine Regel über dem Adapter, kein neuer Adapter.

## Test laufen lassen

```bash
pytest tests/test_branches.py -v
```

Sollte 7 grüne Tests zeigen.
