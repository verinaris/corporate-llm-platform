"""
FastAPI-Hauptanwendung.

Hier kommen alle Router zusammen, hier wird die DB initialisiert.

Start lokal:
    uvicorn app.main:app --reload

Dann öffnen:
    http://localhost:8000/docs    -> Swagger-UI (interaktive API-Doku)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import chat, health, stats
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Wird beim App-Start und -Stop aufgerufen."""
    # Startup
    init_db()
    yield
    # Shutdown (nichts zu tun in Phase 1)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    # Router einhängen
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(stats.router)

    return app


app = create_app()
