# ============================================================ #
# Dockerfile für die Corporate LLM Platform (Backend)
# ============================================================ #
# Multi-Stage-Build → schlankes Image, kein Build-Tooling im
# finalen Container. Läuft als nicht-root User.
#
# Build:
#   docker build -t corporate-llm-platform:latest .
#
# Run (mit .env-Datei):
#   docker run --rm -p 8000:8000 --env-file .env \
#       -v $(pwd)/data:/app/data \
#       corporate-llm-platform:latest
# ============================================================ #

# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Build-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.12-slim

WORKDIR /app

# Nicht-root User anlegen
RUN groupadd -r app && useradd -r -g app -d /app -s /bin/bash app

# Python-Pakete global aus Builder uebernehmen (kompletter site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# App-Code
COPY --chown=app:app app /app/app
COPY --chown=app:app streamlit_app /app/streamlit_app

# Data-Verzeichnis (für SQLite — in Produktion durch Volume mounten)
RUN mkdir -p /app/data && chown app:app /app/data

USER app

EXPOSE 8000

# Healthcheck — k8s/Docker können erkennen ob die App noch lebt
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Backend starten (Streamlit braucht später ein separates Image / Service)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
