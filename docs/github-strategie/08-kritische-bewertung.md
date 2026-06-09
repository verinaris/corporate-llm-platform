# 08 — Kritische Bewertung: Risiken & Gegenmaßnahmen

> **Leitprinzip:** Strategie ohne kritische Selbst-Bewertung ist Marketing.
> Hier benenne ich ehrlich die Schwächen — und wie wir sie entschärfen.

---

## 🔴 Hoch-priorisierte Risiken

### 1. "Vollständig KI-augmentiert"-Problem

**Risiko:** Bei genauer Betrachtung des `corporate-llm-platform`-Repos erkennen technisch versierte Reviewer, dass viel Code mit Claude-Code-Hilfe entstanden ist. Das ist heute nicht mehr problematisch — wenn man's nicht versteckt.

**Konkrete Gefahr:**
- Reviewer denkt: *"Sascha kann den Code nicht selbst lesen / pflegen"*
- Verlust an Glaubwürdigkeit als technischer Berater

**Gegenmaßnahmen:**
- ✅ **Transparenz schlägt Versteckspiel:** In README erwähnen *"This codebase was built with AI assistance as a deliberate showcase of human-in-the-loop development."*
- ✅ Die **Architektur-Entscheidungen** sind sichtbar deine (Branchen-Profile, Audit-Strategie, Provider-Abstraktion)
- ✅ **Lessons Learned** und Phase-Dokumentation zeigen Reflexion, die nur ein Mensch leisten kann
- ⚠️ **In Kundengesprächen ehrlich sein:** "Ich orchestriere KI-Code — nicht weil ich keinen schreiben kann, sondern weil das die zukünftige Arbeit ist."

### 2. Compliance-Aussagen ohne Anwalts-Backing

**Risiko:** Repos beziehen sich auf HWG, DSGVO, EU AI Act, BSI-Grundschutz. Bei juristisch ungenauen Formulierungen → **Haftungsproblem**.

**Konkrete Gefahr:**
- Jemand setzt deine Compliance-Vorlagen ohne Anwalt ein, hat Schaden → Vorwurf der Falschberatung
- Beratungs-Kollegen mit juristischem Hintergrund finden Ungenauigkeiten

**Gegenmaßnahmen:**
- ✅ **Disclaimer in jedem Repo:** "Ersetzt keine anwaltliche / steuerliche / DSB-Beratung. Vorlagen mit eigener Compliance-Funktion prüfen."
- ✅ **Vorlagen-Sprache neutral halten:** Statt *"DSGVO-konform"* schreibe *"DSGVO-orientiert"* oder *"vorbereitet für DSGVO-Prüfung"*
- ✅ **Daten in Quelltexten:** auch ältere Whitepaper datieren, damit überholte Inhalte erkennbar sind
- ⚠️ **MIT-Lizenz mit "no warranty"** verstärkt rechtliche Distanz
- ⚠️ **Bei großen Mandaten** Pharma-/Steuer-Anwalt im Beirat oder als Reviewer einbinden

### 3. Showcase-Repo als Single Point of Failure

**Risiko:** Wenn `corporate-llm-platform` als einziges Substanz-Repo da ist und einen Bug oder Sicherheitsproblem hat → **gesamtes Profil leidet**.

**Konkrete Gefahr:**
- Im RAG-Service ist eine Prompt-Injection-Lücke → öffentliches Issue → "Sicherheitsberater hat selbst Lücke"
- Eine fehlerhafte Compliance-Aussage in der Plattform wird zitiert

**Gegenmaßnahmen:**
- ✅ **GitHub Secret Scanning + Dependabot** aktivieren (`05-security-checkliste.md`)
- ✅ **SECURITY.md** mit Disclosure-Pfad in jedem Repo
- ✅ **CHANGELOG.md** in Phase 2 ergänzen (zeigt aktive Wartung)
- ✅ Mindestens **2-3 Substanz-Repos** in den ersten 90 Tagen (siehe 07-90-tage-plan)
- ⚠️ **Niemals "Production-Ready"** behaupten — immer "active development, not production-hardened"

### 4. Pharma-Branchenfokus zu eng

**Risiko:** Du baust stark auf Pharma — wenn der Pharma-Lead nicht zustande kommt oder die Pharma-Welt sich verändert (Regulierung, M&A), ist die Positionierung zu eng.

**Gegenmaßnahmen:**
- ✅ Plattform-Architektur ist **branchenagnostisch** (`User.branch`) — das ist genau dein Hebel
- ✅ Im Profil: *"für regulierte KMU"* statt *"für Pharma"*
- ✅ 2. Branchen-Profil (Anwalt oder Steuer) in Wochen 9-12 bauen → Skalierbarkeit beweisen
- ⚠️ Energie/Bundeswehr-nah als Sekundär-Zielgruppen offen halten

---

## 🟡 Mittel-priorisierte Risiken

### 5. Profil wirkt wie "Berater mit GitHub-Hobby"

**Risiko:** Du bist Berater **und** baust Code. Externe könnten das als "Hobby" statt "Profession" lesen.

**Gegenmaßnahmen:**
- ✅ **Substanz im Showcase** spricht für sich (146 Tests, 6 Phasen, klare Doku)
- ✅ **Lessons Learned mit Datum** zeigen kontinuierliche Arbeit
- ✅ **Wöchentliche Commits** in Wochen 5-12 demonstrieren Ernsthaftigkeit
- ⚠️ **Nicht "ich code abends"** kommunizieren — sondern "ich nutze Code als Beratungs-Werkzeug"

### 6. Recruiter-Spam

**Risiko:** Wenn das Profil "auffällt", melden sich **Recruiter** mit irrelevanten Anfragen (Senior-Python-Dev, ML-Engineer etc.) — das ist Ablenkung.

**Gegenmaßnahmen:**
- ✅ **Profil-Bio klar positionieren** als *"Berater"*, nicht *"Engineer"*
- ✅ **Keine Programmiersprachen-Liste** im Profil
- ✅ **Verfügbarkeit klar formulieren:** *"Available for: Beratungsmandate, Sparring, Strategie-Workshops"*
- ⚠️ Standardisierte Absage-Vorlage für Recruiter vorbereiten

### 7. Plagiat-/Idea-Theft-Sorge

**Risiko:** Deine Vorlagen, Architektur-Patterns und Whitepaper werden von Konkurrenten 1:1 übernommen.

**Gegenmaßnahmen:**
- ✅ **Datum + Autor** in jedem Whitepaper (Beleg für Priorität)
- ✅ **CC-BY 4.0 für Vorlagen** zwingt Namens-Nennung
- ✅ **Eigene Architektur-Begriffe** etablieren (z.B. "Branchen-Profile als 1. Klasse Bürger")
- ⚠️ **Code-Plagiat ist sekundär** — Beratungs-Mandate gewinnt man durch Person, nicht durch Code-Vorlagen

### 8. Zeit-Budget unrealistisch

**Risiko:** Der 90-Tage-Plan rechnet mit ~4h/Woche. Wenn Kunden-Mandate dazwischen kommen, bleibt nichts liegen — außer GitHub.

**Gegenmaßnahmen:**
- ✅ **Minimum-Viable-Profil nach 4 Wochen** — danach kann es 2 Monate ruhen ohne Schaden
- ✅ **Wöchentliche Reflexion in Tabellenform** — Versäumnisse werden sichtbar
- ⚠️ **Plan flexibel anpassen** — lieber 6 Monate für 90-Tage-Plan als nie fertig
- ⚠️ **Keine Streak-Pressure** — GitHub-Streaks sind ein psychologischer Trick

---

## 🟢 Niedrig-priorisierte Risiken

### 9. Bundeswehr-Nähe könnte polarisieren

**Risiko:** Erwähnung "bundeswehr-nahe Organisationen" als Zielgruppe könnte Pharma-/Wissenschafts-Kunden abschrecken (oder umgekehrt).

**Gegenmaßnahmen:**
- ✅ Im Public-Profil **breiter formulieren:** "öffentliche Auftraggeber" statt explizit Bundeswehr
- ⚠️ Bundeswehr-Nähe gehört in LinkedIn-Erfahrung, nicht ins GitHub-Profil

### 10. Streamlit als Frontend wirkt "prototyp-ig"

**Risiko:** Technische Reviewer sehen Streamlit und denken "MVP-Stack" statt "produktiv-bereite Plattform".

**Gegenmaßnahmen:**
- ✅ **Im README transparent:** *"Streamlit für schnelle Iteration, Next.js/shadcn geplant für Phase 8"*
- ✅ **Wert der Architektur** betonen: Backend (FastAPI) ist Frontend-agnostisch
- ⚠️ **Roadmap zeigt:** Frontend-Migration als bewusste Phase

### 11. Sole-Maintainer-Risiko

**Risiko:** Profil/Repos hängen 100% an dir. Bei längerer Pause (Krankheit, Urlaub, Wechsel) wirkt das Profil "tot".

**Gegenmaßnahmen:**
- ✅ **Datierung** in Whitepaper macht Pausen transparent
- ✅ **Kein "letzte Aktualisierung: gestern"** im Bio — Vermeidung künstlicher Aktualitäts-Pressure
- ⚠️ **Kollege/Sparring-Partner** als Outside-Collaborator für Notfälle

---

## 📊 Risiko-Matrix (zusammengefasst)

| # | Risiko | Eintrittswahrscheinlichkeit | Schadensausmaß | Restrisiko nach Maßnahmen |
|---|---|---|---|---|
| 1 | KI-augmentiert-Wahrnehmung | hoch | mittel | 🟡 niedrig (mit Transparenz) |
| 2 | Compliance-Aussagen ohne Anwalt | mittel | hoch | 🟡 mittel (Disclaimer + neutrale Sprache) |
| 3 | Showcase als Single-Point-of-Failure | niedrig | hoch | 🟢 niedrig |
| 4 | Pharma-Fokus zu eng | mittel | mittel | 🟢 niedrig (mit 2. Branche) |
| 5 | "Hobby"-Wahrnehmung | mittel | mittel | 🟢 niedrig |
| 6 | Recruiter-Spam | hoch | niedrig | 🟢 sehr niedrig |
| 7 | Plagiat-Sorge | mittel | niedrig | 🟢 sehr niedrig |
| 8 | Zeit-Budget reisst | hoch | mittel | 🟡 mittel (Plan-Flexibilität) |
| 9 | Bundeswehr-Polarisierung | niedrig | niedrig | 🟢 sehr niedrig |
| 10 | Streamlit "prototyp-ig" | mittel | niedrig | 🟢 niedrig |
| 11 | Sole-Maintainer | niedrig | mittel | 🟢 niedrig |

---

## 🛡️ Reputations-spezifische Risiken

Diese verdienen separate Aufmerksamkeit, weil sie nicht durch technische Maßnahmen behebbar sind:

### Veröffentlichung eines kontroversen Whitepapers
**Gegenmaßnahme:**
- 24h Reflexion-Regel vor Publishing
- Wenn unsicher → Person des Vertrauens vorab lesen lassen
- "Wer ist das anvisierte Lese-Publikum?" als Frage vor jedem Post

### Cross-Posting auf LinkedIn mit aggressiver Botschaft
**Gegenmaßnahme:**
- LinkedIn-Posts neutral, GitHub-READMEs neutral
- Politische / Branchen-kritische Inhalte nur in `thought-leadership` und mit klarer Datierung

### Ehemalige Arbeitgeber / Mandanten erwähnen
**Gegenmaßnahme:**
- ✅ **NIE** namentlich ohne schriftliche Freigabe
- ✅ Anonymisierte Lessons Learned ("Bei einem Pharma-Mandant…")
- ⚠️ Auch in der Vergangenheit liegende Mandate können noch heikel sein

---

## 🎯 Empfehlung

**Drei nicht-verhandelbare Regeln** für die ersten 90 Tage:

1. **Security-Checkliste vor JEDEM Push** (`05-security-checkliste.md`)
2. **24h-Reflexion vor JEDEM Whitepaper** zu kontroversen Themen
3. **Quartals-Self-Audit:** alle veröffentlichten Repos einmal durchgehen

Wenn diese drei Regeln eingehalten werden, sind die meisten oben genannten Risiken auf **vertretbares Niveau** reduziert.

---

## 💡 Ehrliche Schluss-Wertung

Diese GitHub-Strategie ist **gut, aber nicht magisch**. Sie wird dir:

✅ Beim ersten Kunden-Termin helfen ("schauen Sie mal hier")
✅ Recruiter-Anfragen filtern
✅ Im Beratungs-Netzwerk Reputation aufbauen
✅ Methodik dokumentieren, die du sowieso anwendest

❌ Keine Massen-Lead-Generation bringen
❌ Keine Konkurrenz zu etablierten Beratungs-Marken machen
❌ Keine viralen Effekte produzieren

**Der ehrliche Pitch:** GitHub-Profil ist ein **Vertrauens-Anker**, kein Akquise-Motor. Mit dieser Erwartung lohnt sich der Aufwand. Mit der falschen Erwartung führt er zur Frustration.

---

*Letzte Bewertung: Juni 2026 · Stand der Plattform: nach Phase 6a (Audit-Log + DSGVO)*
