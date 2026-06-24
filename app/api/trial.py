"""
Trial-API — Endpoints für Trial-Status.

Bewusst OHNE Authentifizierung, da auch das Login-Fenster den Status
anzeigen muss. Der Trial-Status ist keine sensible Information.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.services import trial as trial_service


router = APIRouter(prefix="/trial", tags=["trial"])


@router.get("/status")
def get_trial_status(session: Session = Depends(get_session)):
    """
    Liefert den aktuellen Trial-Status der Verinaris-Instanz.

    Bewusst öffentlich (keine Auth), damit das Login-Fenster den Status
    anzeigen kann.

    Returns:
        {
            "status": "active" | "expiring_soon" | "expired" | "licensed",
            "days_remaining": int,
            "hours_remaining": int,
            "installed_at": ISO-Date,
            "expires_at": ISO-Date,
            "message": str,
        }
    """
    try:
        return trial_service.get_status(session)
    except ValueError as exc:
        # TrialState nicht initialisiert — sollte nie passieren,
        # aber defensiv abfangen
        raise HTTPException(
            status_code=503,
            detail=f"Trial-Status nicht verfügbar: {exc}",
        )
