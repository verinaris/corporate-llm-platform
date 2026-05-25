"""
Stats-Endpoint (geschützt).

Admins sehen Stats aller User. Normale User sehen nur ihre eigenen.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import User, UserRole
from app.schemas import StatsSummary
from app.services import token_tracker

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsSummary)
def stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StatsSummary:
    """Gesamtauswertung — global für Admin, eigene für User."""
    if current_user.role == UserRole.ADMIN:
        user_filter = None  # alle User
    else:
        user_filter = current_user.email
    return token_tracker.get_summary(session, user_filter=user_filter)
