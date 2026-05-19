# Auswertung: Token- & Streak-Verbrauch Bauphase

Diese Datei dokumentiert den Aufwand, der für die Phasen 0 + 1 angefallen ist — als Lerngrundlage und zur Kostenabschätzung für weitere Phasen.

## Was ist ein "Token"?

Ein Token ist die kleinste Verarbeitungseinheit eines LLM — in etwa **3–4 Zeichen** oder **¾ eines Wortes** im Durchschnitt. "Hallo Welt" sind ungefähr 3 Tokens.

**Analogie:** Wie Buchstaben für einen Setzer in der Druckerei — du bezahlst nach Anzahl Buchstaben, nicht nach Wörtern.

## Was ist ein "Streak" (Klärung der Begrifflichkeit)

In Claude-Kontexten wird "Streak" meist gleichgesetzt mit:
- **Message-Streak** = Anzahl Nachrichten in Folge innerhalb eines Limit-Zeitfensters
- bei Claude.ai Pro/Team gibt es Nutzungslimits, die sich nach Tokens *und* Anzahl Nachrichten richten

> **Ehrlicher Hinweis:** Ich habe **keinen Live-Zugriff** auf deine konkreten Claude.ai-Verbrauchszahlen oder dein Streak-Limit. Diese Werte siehst du in deinen Account-Einstellungen. Ich kann nur **schätzen**, wie viel diese Bauphase ungefähr verbraucht hat.

## Schätzung dieser Session (Phasen 0 + 1)

| Metrik | Geschätzter Wert |
|--------|------------------|
| Erstellte Dateien | 24 |
| Codezeilen (ohne Doku) | ~ 550 |
| Dokumentationszeilen | ~ 600 |
| Ein-/Ausgabe-Tokens (Konversation) | ~ 35.000 – 50.000 |
| Konversations-Turns (Streak) | 5 |

> Der genaue Wert hängt vom Anbieter und Tokenizer ab — die Range ist eine grobe Hausnummer.

## Hochrechnung für die nächsten Phasen

Falls dein Plan ist, das Projekt **innerhalb von Claude.ai** weiterzubauen:

| Phase | Geschätzter Token-Aufwand | Geschätzte Turns |
|-------|---------------------------|------------------|
| 2 — Streamlit + Auth | 30 – 50k | 4 – 6 |
| 3 — RAG (komplexer) | 50 – 80k | 6 – 10 |
| 4 — Multi-LLM | 20 – 30k | 3 – 5 |
| 5 — Dashboard | 25 – 40k | 4 – 6 |
| **Summe Phase 2–5** | **125 – 200k Tokens** | **17 – 27 Turns** |

## Auswertung deiner echten API-Verbräuche (laufender Betrieb)

Sobald deine Plattform läuft, liefert sie selbst die Verbrauchs-Auswertung — über den Endpoint:

```
GET http://localhost:8000/stats
```

Dort siehst du:
- Anzahl Requests gesamt + pro User + pro Modell
- Tokens (input/output/gesamt)
- Kosten in USD

Diese Werte stammen aus deiner SQLite (`data/platform.db`) und sind **real**, nicht geschätzt.

## Limit-Übersicht Claude.ai (zur Orientierung)

Da ich keinen Live-Zugriff auf aktuelle Plan-Details habe: Schau für deinen konkreten Plan unter https://support.claude.com/ oder in deinen Account-Einstellungen nach "Usage" / "Limits".

Wichtig: Die **API** (für deine Plattform) und **Claude.ai** (dieses Chat-Interface) haben **getrennte** Limits und Abrechnungen.
