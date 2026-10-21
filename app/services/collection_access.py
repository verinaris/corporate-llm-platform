"""
Mandantentrennung: Zugriffsstufen aus der Datenbank ermitteln.

Die Regel selbst steht in app/auth/permissions.py (reine Funktionen).
Hier wird nur nachgeschlagen: Wem gehoert die Sammlung, ist der User
Mitglied, ist sie fuer alle lesbar?

Eine Sammlung ohne Eintrag in document_collections gilt als
nicht vorhanden und damit als geschlossen.
"""

from typing import Optional

from sqlmodel import Session, select

from app.auth.permissions import can_read_collection, collection_level
from app.models import CollectionMember, DocumentCollection, User


def get_collection_level(session: Session, user: User, name: str) -> Optional[str]:
    """Stufe des Users fuer die Sammlung: owner/maintain/read oder None."""
    coll = session.get(DocumentCollection, name)
    if coll is None:
        return None
    member = session.exec(
        select(CollectionMember).where(
            CollectionMember.collection == name,
            CollectionMember.user_id == user.id,
        )
    ).first()
    return collection_level(
        user.email,
        coll.created_by,
        member.level if member else None,
        coll.open_for_all,
    )


def readable_collections(session: Session, user: User) -> set[str]:
    """Alle Sammlungsnamen, die der User lesen darf."""
    collections = session.exec(select(DocumentCollection)).all()
    members = {
        m.collection: m.level
        for m in session.exec(
            select(CollectionMember).where(CollectionMember.user_id == user.id)
        ).all()
    }
    return {
        c.name
        for c in collections
        if can_read_collection(
            collection_level(user.email, c.created_by, members.get(c.name), c.open_for_all)
        )
    }


# ----------------------------------------------------------------------- #
# Tuersteher: harte Pruefung mit Audit
# ----------------------------------------------------------------------- #
#
# Bewusst DIESELBE Meldung fuer "gibt es nicht" und "gesperrt": sonst liesse
# sich durch Ausprobieren herausfinden, welche Mandanten-Sammlungen existieren.

from fastapi import HTTPException  # noqa: E402

from app.auth.permissions import can_maintain_collection  # noqa: E402
from app.models import AuditAction  # noqa: E402
from app.services import audit  # noqa: E402


def _role_value(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


def _log_denied(user: User, name: str, need: str) -> None:
    audit.log(
        user_email=user.email,
        action=AuditAction.COLLECTION_ACCESS_DENIED,
        user_role=_role_value(user.role),
        target_type="collection",
        target_id=name,
        details={"need": need},
    )


def _allowed(level: Optional[str], need: str) -> bool:
    if need == "maintain":
        return can_maintain_collection(level)
    return can_read_collection(level)


def require_collection_access(
    session: Session, user: User, name: str, need: str = "read"
) -> str:
    """Liefert die Stufe oder wirft 403 (mit Audit). need = 'read' | 'maintain'."""
    level = get_collection_level(session, user, name)
    if not _allowed(level, need):
        _log_denied(user, name, need)
        raise HTTPException(
            status_code=403,
            detail=f"Kein Zugriff auf die Sammlung '{name}'.",
        )
    return level


def require_upload_target(session: Session, user: User, name: str) -> str:
    """
    Darf der User in diese Sammlung hochladen?

    Neue Sammlung: ja, er wird ihr Besitzer (siehe _upsert_collection_meta).
    Bestehende Sammlung: nur mit Stufe 'maintain' oder als Besitzer.
    """
    if session.get(DocumentCollection, name) is None:
        return "new"
    return require_collection_access(session, user, name, need="maintain")


def has_collection_access(
    session: Session, user_id: Optional[int], name: str, need: str = "read"
) -> bool:
    """Variante ohne HTTP fuer Tools. Ohne bekannten User: kein Zugriff."""
    user = session.get(User, user_id) if user_id else None
    if user is None:
        return False
    if _allowed(get_collection_level(session, user, name), need):
        return True
    _log_denied(user, name, need)
    return False
