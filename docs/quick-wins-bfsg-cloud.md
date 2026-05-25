# BFSG + Cloud-Readiness — Quick Wins

Was wir **jetzt** schon gemacht haben, um später nicht alles umbauen zu müssen.

---

## 🌐 Accessibility (BFSG / EAA / WCAG 2.1 AA)

### Was wurde umgesetzt

| Quick Win | Datei | Effekt |
|-----------|-------|--------|
| Sprache `de` setzen | `streamlit_app/app.py` | Screen-Reader lesen Deutsch korrekt aus |
| Kontrastreicher Default-Theme | `.streamlit/config.toml` | WCAG 1.4.3 Contrast Minimum (4.5:1) |
| Verbesserter Focus-Ring | `streamlit_app/app.py` (CSS) | WCAG 2.4.7 Focus Visible |
| Telemetrie aus | `.streamlit/config.toml` | DSGVO — Streamlit sendet keine Usage-Daten mehr |

### Was später kommt (Phase 5-6)

- Audit mit Lighthouse + axe-core
- Tastatur-Navigation kompletter Workflow durchklicken
- Alternative für Custom-Streamlit-Komponenten
- Eventuell Wechsel zu Next.js + shadcn/ui für vollen WCAG-Support

### Was ist BFSG?

- **Barrierefreiheitsstärkungsgesetz** (Deutschland)
- Setzt **EU AI Act** (richtig: **European Accessibility Act**) um
- Gilt seit **28.06.2025**
- Hauptpflicht: WCAG 2.1 AA-Konformität für **B2C**-Dienstleistungen
- B2B-only-Tools sind teilweise befreit, aber best-practice-mäßig sollte man's einhalten

---

## ☁️ Cloud-Readiness

### Was wurde umgesetzt

| Quick Win | Datei | Effekt |
|-----------|-------|--------|
| **Anthropic Base-URL konfigurierbar** | `app/config.py`, `anthropic_client.py` | Später EU-Region per `.env` aktivieren: `ANTHROPIC_BASE_URL=https://api.eu.anthropic.com` |
| **Production-Validation** | `app/config.py` | Bei `APP_ENV=production` muss JWT_SECRET stark und Debug aus |
| **APP_ENV-Auswahl** | `app/config.py` | `development` / `staging` / `production` — Pydantic validiert |
| **CORS-Konfiguration vorbereitet** | `app/config.py` | Wenn Frontend & Backend auf verschiedenen Hosts laufen |
| **Dockerfile (Backend)** | `Dockerfile` | Multi-Stage, non-root, healthcheck — ready für k8s |
| **.dockerignore** | `.dockerignore` | Keine `.env`, kein `data/`, kein `.git` im Image |
| **docker-compose.yml** | `docker-compose.yml` | Lokales Test-Setup mit `docker compose up` |

### Was später kommt (Phase 6)

- **PostgreSQL** statt SQLite (managed durch Provider)
- **Vector-DB** (Qdrant Cloud oder self-hosted)
- **Streamlit-Image** als zweiter Service in docker-compose
- **TLS/HTTPS** via Reverse Proxy (Caddy / Traefik)
- **Secret-Management** über Provider-Vault (statt `.env`-File)
- **Monitoring** (Prometheus + Grafana)
- **Strukturiertes Logging** (JSON)

### Provider-Optionen für EU-Hosting

Siehe Kommentare im `BACKLOG.md`. Top-Tipp für ersten Test: **Hetzner Cloud** (günstig, DE-Standort, Docker-tauglich).

---

## Production-Mode-Check vor Deployment

Setze in `.env`:
```
APP_ENV=production
APP_DEBUG=false
JWT_SECRET=<mindestens 32 zufällige Zeichen>
ANTHROPIC_BASE_URL=https://api.eu.anthropic.com
```

Wenn beim Start *nichts* gemeckert wird → grünes Licht für Production.
Wenn ein Fehler kommt: Pydantic zeigt dir genau, was fehlt.
