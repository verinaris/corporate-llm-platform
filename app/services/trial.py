"""
TrialService — Berechnet den Trial-Status der Verinaris-Instanz.

Vier Zustände:
- ACTIVE         → Mehr als 24h Trial-Zeit übrig
- EXPIRING_SOON  → Weniger als 24h übrig
- EXPIRED        → Trial vorbei (sanfter Hinweis, keine Sperre!)
- LICENSED       → Aktive Lizenz vorhanden (Phase 2)

Verwendung:
    from app.services import trial
    status = trial.get_status(session)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Session, select

from app.models import TrialState


# ====================================== #
# Enums + Konstanten
# ====================================== #


class TrialStatus(str, Enum):
    """Möglicher Status der Verinaris-Instanz."""

    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    LICENSED = "licensed"


EXPIRING_SOON_HOURS = 24  # Schwellwert für "letzter Tag"


# ====================================== #
# Hilfsfunktionen
# ====================================== #


def _ensure_utc(dt: datetime) -> datetime:
    """
    Stellt sicher, dass ein datetime-Objekt UTC-aware ist.

    SQLite speichert datetimes naiv — wir machen sie für Vergleiche
    timezone-aware. Das verhindert TypeError beim Subtrahieren.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_trial_state(session: Session) -> Optional[TrialState]:
    """Holt den aktuellen TrialState (es gibt immer nur 1 Zeile)."""
    return session.exec(select(TrialState)).first()


# ====================================== #
# Hauptfunktion: Status-Berechnung
# ====================================== #


def get_status(session: Session) -> dict:
    """
    Liefert den aktuellen Trial-Status für UI/API.

    Returns:
        {
            "status": "active" | "expiring_soon" | "expired" | "licensed",
            "days_remaining": int,
            "hours_remaining": int,
            "installed_at": ISO-Date,
            "expires_at": ISO-Date,
            "message": str,
        }

    Raises:
        ValueError: Wenn TrialState nicht initialisiert wurde
    """
    state = get_trial_state(session)
    if not state:
        raise ValueError(
            "TrialState ist nicht initialisiert. Wurde init_db() aufgerufen?"
        )

    now = datetime.now(timezone.utc)
    installed_at = _ensure_utc(state.installed_at)
    expires_at = _ensure_utc(state.expires_at)
    license_valid_until = (
        _ensure_utc(state.license_valid_until) if state.license_valid_until else None
    )

    # Lizenz hat Vorrang
    if license_valid_until and license_valid_until > now:
        remaining = license_valid_until - now
        return {
            "status": TrialStatus.LICENSED,
            "days_remaining": remaining.days,
            "hours_remaining": int(remaining.total_seconds() / 3600),
            "installed_at": installed_at.isoformat(),
            "expires_at": license_valid_until.isoformat(),
            "message": "Lizenzierte Version aktiv.",
        }

    # Trial-Logik
    remaining = expires_at - now
    days = remaining.days
    hours = int(remaining.total_seconds() / 3600)

    # EXPIRED
    if hours < 0:
        return {
            "status": TrialStatus.EXPIRED,
            "days_remaining": 0,
            "hours_remaining": 0,
            "installed_at": installed_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "message": (
                "Die 7-tägige Testphase ist beendet. "
                "Für die weitere Nutzung kontaktieren Sie sascha@verinaris.de"
            ),
        }

    # EXPIRING_SOON
    if hours < EXPIRING_SOON_HOURS:
        return {
            "status": TrialStatus.EXPIRING_SOON,
            "days_remaining": 0,
            "hours_remaining": hours,
            "installed_at": installed_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "message": (
                f"⚠️ Letzter Tag der Testphase ({hours}h verbleibend). "
                "Kontakt für Lizenz: sascha@verinaris.de"
            ),
        }

    # ACTIVE
    return {
        "status": TrialStatus.ACTIVE,
        "days_remaining": days,
        "hours_remaining": hours,
        "installed_at": installed_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "message": f"Verinaris Testversion — {days} Tage verbleibend.",
    }
