"""Health-Check-Endpoints."""

from fastapi import APIRouter

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Einfacher Liveness-Check — antwortet immer, wenn die App läuft."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": __version__,
    }
