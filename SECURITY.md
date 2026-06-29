# 🛡️ Security Policy

## Verantwortungsvolle Offenlegung von Schwachstellen

Wenn Sie eine Sicherheitslücke in dieser Plattform entdecken, bitte ich um **verantwortungsvolle Offenlegung** — kein öffentliches Issue, sondern eine direkte Mitteilung.

### Kontakt
**E-Mail:** s_mkern@t-online.de
**Betreff:** `[SECURITY] Corporate LLM Platform — kurze Beschreibung`

### Was bitte mitsenden
- **Schritt-für-Schritt-Reproduktion** der Lücke
- **Betroffene Version / Commit-Hash**
- **Erwartete vs. tatsächliche Auswirkung**
- Ihre **Kontaktdaten** für Rückfragen
- Optional: einen Vorschlag zur Behebung

### Was passiert dann
1. **Innerhalb 48h** Eingangsbestätigung
2. **Innerhalb 2 Wochen** initiale Bewertung
3. **Koordinierte Veröffentlichung** nach Patch — Credit an Sie (falls gewünscht)

---

## Was als Sicherheitslücke gilt

### 🚨 Hoch-priorisierte Befunde

- **Authentifizierungs-Bypass** (Login umgehen, falsche Rolle erlangen)
- **Daten-Leak** zwischen Tenants/Usern (DSGVO Art. 32 — Vertraulichkeit)
- **Sensitive Daten in Logs** (API-Keys, Passwörter, personenbezogene Daten)
- **JWT-Schwachstellen** (Token-Manipulation, schwache Secrets)
- **SQL-Injection / NoSQL-Injection**
- **Server-Side Request Forgery (SSRF)** über RAG-Quellen-Fetching
- **Prompt-Injection** mit Auswirkung auf andere Nutzer
- **Audit-Log-Manipulation** (Compliance-relevant)

### 🟡 Mittel-priorisierte Befunde

- **Cross-Site Scripting (XSS)** in Streamlit-Komponenten
- **CSRF** in Admin-Aktionen
- **Information Disclosure** über Fehlermeldungen
- **Dependency-Schwachstellen** (CVEs in `requirements.txt`)
- **Race Conditions** bei kritischen Operationen

### 🟢 Niedrig-priorisierte / Out-of-Scope

- **Rate-Limiting-Findings** — aktuell bewusst nicht aktiviert für lokalen Betrieb
- **DoS-Szenarien** durch große Uploads ohne Auth
- **Findings in Demo-/Beispiel-Daten**

---

## Bekannte Einschränkungen (transparent gelistet)

Diese Plattform ist **aktiv in Entwicklung** und bewusst noch nicht produktions-gehärtet. Bekannte Limitierungen:

| Bereich | Aktueller Stand | Geplante Verbesserung |
|---|---|---|
| TLS / HTTPS | Lokal nur HTTP | Phase 8: Caddy/Traefik Reverse-Proxy |
| Rate-Limiting | Nicht aktiviert | Phase 8: `slowapi` |
| Pentest | Nicht durchgeführt | vor Produktivnutzung |
| 2FA | Nicht implementiert | Wishlist |
| Passwort-Reset | Nur via Admin-API | Wishlist |
| Backup-Verschlüsselung | SQLite unverschlüsselt | Phase 8: PostgreSQL TDE |

**Für Produktivbetrieb** ist eine individuelle Härtung notwendig — siehe README für Beratungs-Kontakt.

---

## DSGVO + EU AI Act

Diese Plattform implementiert bewusst:
- **DSGVO Art. 15** — Auskunftsrecht (Datenexport in einem Klick)
- **DSGVO Art. 17** — Recht auf Vergessenwerden mit Pseudonymisierung
- **DSGVO Art. 30** — Audit-Trail vorbereitet
- **EU AI Act Art. 13** — Transparenz (Quellen-Pflicht im RAG)

Bei Compliance-Fragen oder DSB-Anfragen: kontaktieren Sie mich direkt.

---

## Anerkennungen

Für verantwortungsvolle Offenlegung Anerkennung in einer "Hall of Thanks" — auf Wunsch namentlich oder anonym.

---

*Stand: Juni 2026*
