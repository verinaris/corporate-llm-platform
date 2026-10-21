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
