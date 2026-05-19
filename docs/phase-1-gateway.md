# Phase 1 — API-Gateway mit Token-Logging

**Ziel:** Eine lauffähige API, die Chat-Anfragen an Claude weiterreicht und jeden Request mit Token-Verbrauch und Kosten loggt.

## Was wurde gebaut?

### 1. FastAPI-Backend (`app/main.py`)
Drei Endpoints:
- `GET /health` — Liveness-Check
- `POST /chat` — Chat-Anfrage an LLM
- `GET /stats` — Token-/Kostenauswertung

### 2. LLM-Abstraktion (`app/llm/`)
- `BaseLLMClient` — abstraktes Interface
- `AnthropicClient` — konkrete Implementierung für Claude

> **Warum Abstraktion?** In Phase 4 kommen OpenAI und Ollama dazu. Mit der Basis-Klasse muss der Rest der App **nicht angepasst** werden.

**Analogie:** Steckdose mit Adapter-Slot. Der Strom (= LLMResponse) ist immer gleich, egal welcher Anbieter "im Hintergrund" liefert.

### 3. Token-Tracker (`app/services/token_tracker.py`)
Schreibt nach jedem Request eine Zeile in die `token_usage`-Tabelle:

| Feld | Beispiel |
|------|----------|
| timestamp | 2026-05-14T10:30:00Z |
| user_id | "alice" |
| provider | "anthropic" |
| model | "claude-sonnet-4-6" |
| input_tokens | 25 |
| output_tokens | 142 |
| total_tokens | 167 |
| cost_usd | 0.002205 |
| latency_ms | 1234 |
| success | true |

### 4. Preistabelle (`app/pricing.py`)
Berechnet pro Request die Kosten anhand des verwendeten Modells:

```python
cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
```

> **Wichtig:** Die Preise sind Schätzwerte. Für Produktion regelmäßig gegen die offiziellen Preisseiten abgleichen.

## Ablauf eines Requests

```
Client                FastAPI              AnthropicClient        Anthropic
  |                      |                       |                    |
  |--POST /chat--------->|                       |                    |
  |                      |--validate(schema)     |                    |
  |                      |--resolve client------>|                    |
  |                      |                       |--API call--------->|
  |                      |                       |<---response--------|
  |                      |<--LLMResponse---------|                    |
  |                      |--log to SQLite                            |
  |<--ChatResponse-------|                                            |
```

## Ausprobieren

### Starten
```bash
uvicorn app.main:app --reload
```

### Erstes Request
Öffne http://localhost:8000/docs → `POST /chat` → "Try it out":

```json
{
  "messages": [
    {"role": "system", "content": "Du antwortest immer auf Deutsch."},
    {"role": "user", "content": "Erkläre Token in einem Satz."}
  ],
  "user_id": "max-mustermann"
}
```

### Auswertung abrufen
```
GET http://localhost:8000/stats
```

Beispiel-Antwort:
```json
{
  "total_requests": 3,
  "total_input_tokens": 87,
  "total_output_tokens": 412,
  "total_tokens": 499,
  "total_cost_usd": 0.006441,
  "by_model": {
    "claude-sonnet-4-6": {
      "requests": 3,
      "input_tokens": 87,
      "output_tokens": 412,
      "cost_usd": 0.006441
    }
  },
  "by_user": {
    "max-mustermann": {
      "requests": 3,
      "total_tokens": 499,
      "cost_usd": 0.006441
    }
  }
}
```

## Tests laufen lassen

```bash
pytest
```

Sollte zwei grüne Tests zeigen (`test_health`, `test_stats_initially_empty`).

## Bekannte Limitierungen (Stand Phase 1)

- ❌ **Keine Authentifizierung** — jeder im Netzwerk kann anfragen
- ❌ **Kein Streaming** — Antworten kommen erst, wenn das LLM fertig ist
- ❌ **Nur Anthropic** — OpenAI/Ollama kommen in Phase 4
- ❌ **Kein Frontend** — nur API. Frontend kommt in Phase 2

Diese Punkte sind **bewusst** noch offen — sie werden in den späteren Phasen schrittweise gelöst.

## Nächster Schritt (Phase 2)

Streamlit-Chat-Frontend + User-Login + Rollen (admin/user).
