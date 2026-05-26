"""
FastAPI-Hauptanwendung.

Hier kommen alle Router zusammen, hier wird die DB initialisiert,
hier wird der Bootstrap-Admin angelegt.

Start lokal:
    uvicorn app.main:app --reload

Dann öffnen:
    http://localhost:8000/docs    -> Swagger-UI (interaktive API-Doku)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, select

from app import __version__
from app.api import auth as auth_api
from app.api import chat as chat_api
from app.api import documents as documents_api
from app.api import health as health_api
from app.api import stats as stats_api
from app.api import users as users_api
from app.auth.passwords import hash_password
from app.config import get_settings
from app.database import engine, init_db
from app.models import User, UserBranch, UserRole


def bootstrap_admin() -> None:
    """
    Legt beim ersten Start einen Admin-User an, falls in .env konfiguriert.

    Idempotent: existiert der User schon, passiert nichts.
    """
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.email == settings.bootstrap_admin_email)
        ).first()
        if existing:
            return

        admin = User(
            email=settings.bootstrap_admin_email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role=UserRole.ADMIN,
            branch=UserBranch.GENERIC,
        )
        session.add(admin)
        session.commit()
        print(f"[Bootstrap] Admin-User angelegt: {settings.bootstrap_admin_email}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Wird beim App-Start und -Stop aufgerufen."""
    init_db()
    bootstrap_admin()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.include_router(health_api.router)
    app.include_router(auth_api.router)
    app.include_router(users_api.router)
    app.include_router(chat_api.router)
    app.include_router(stats_api.router)
    app.include_router(documents_api.router)

    return app


app = create_app()
