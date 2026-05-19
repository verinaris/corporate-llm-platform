"""
Stats-Endpoint.

Liefert eine Auswertung der bisherigen Token-Verbräuche und Kosten.
Aufrufbar unter GET /stats.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas import StatsSummary
from app.services import token_tracker

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsSummary)
def stats(session: Session = Depends(get_session)) -> StatsSummary:
    """Gesamtauswertung über alle bisherigen LLM-Requests."""
    return token_tracker.get_summary(session)
