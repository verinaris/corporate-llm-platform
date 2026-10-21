"""
Mandantentrennung: Rechte an Sammlungen verwalten (E4).

Nur fuer Rollen mit can_manage_collection_access (admin). Der Admin sieht
hier ausschliesslich METADATEN (Name, Besitzer, Mitglieder, Sichtbarkeit),
nie Inhalte. Lesen darf er eine Sammlung nur, wenn er sich selbst als
Mitglied eintraegt -- das wird als Notfallzugriff auditiert.

Analogie: die Schluesselausgabe am Empfang. Der Empfang fuehrt das
Schluesselbuch, betritt aber die Raeume nicht.

Endpoints:
- GET    /admin/collections                         Uebersicht
- POST   /admin/collections/{name}/members          Mitglied eintragen/aendern
- DELETE /admin/collections/{name}/members/{email}  Recht entziehen
- PUT    /admin/collections/{name}/visibility       "fuer alle lesbar"
- PUT    /admin/collections/{name}/owner            Besitz uebertragen

HINWEIS: Besitz haengt an DocumentCollection.created_by (E-Mail). Wird je
eine E-Mail-Aenderung fuer User eingebaut, muss sie den Besitz mitziehen.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.documents import _validate_collection_name
from app.auth.dependencies import get_current_user
from app.auth.permissions import can_manage_collection_access
from app.database import get_session
from app.models import (
    AuditAction,
    CollectionAccessLevel,
    CollectionMember,
    DocumentCollection,
    User,
)
from app.services import audit

router = APIRouter(prefix="/admin/collections", tags=["admin-collections"])


# ----------------------------------------------------------------------- #
# Schemas
# ----------------------------------------------------------------------- #

class MemberIn(BaseModel):
    email: str
    level: CollectionAccessLevel = CollectionAccessLevel.READ


class VisibilityIn(BaseModel):
    open_for_all: bool


class OwnerIn(BaseModel):
    email: str


class MemberOut(BaseModel):
    email: str
    level: CollectionAccessLevel
    granted_by: str
    granted_at: datetime


class CollectionAdminOut(BaseModel):
    name: str
    owner: str
    owner_active: bool
    open_for_all: bool
    members: list[MemberOut]


# ----------------------------------------------------------------------- #
# Helfer
# ----------------------------------------------------------------------- #

def _require_manager(user: User = Depends(get_current_user)) -> User:
    if not can_manage_collection_access(user.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin-Rechte erforderlich")
    return user


def _role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _get_collection(session: Session, name: str) -> DocumentCollection:
    name = _validate_collection_name(name)
    coll = session.get(DocumentCollection, name)
    if coll is None:
        raise HTTPException(404, detail="Sammlung nicht gefunden")
    return coll


def _get_user_by_email(session: Session, email: str) -> User:
    user = session.exec(
        select(User).where(func.lower(User.email) == email.strip().lower())
    ).first()
    if user is None:
        raise HTTPException(404, detail=f"Kein User mit der E-Mail '{email}'")
    return user


def _out(session: Session, coll: DocumentCollection) -> CollectionAdminOut:
    owner = session.exec(
        select(User).where(func.lower(User.email) == (coll.created_by or "").lower())
    ).first()
    rows = session.exec(
        select(CollectionMember, User)
        .where(CollectionMember.collection == coll.name)
        .where(CollectionMember.user_id == User.id)
    ).all()
    return CollectionAdminOut(
        name=coll.name,
        owner=coll.created_by,
        owner_active=bool(owner and owner.is_active),
        open_for_all=bool(coll.open_for_all),
        members=[
            MemberOut(email=u.email, level=m.level, granted_by=m.granted_by, granted_at=m.granted_at)
            for m, u in rows
        ],
    )


def _audit(admin: User, action: AuditAction, name: str, details: dict) -> None:
    audit.log(
        user_email=admin.email,
        action=action,
        user_role=_role(admin),
        target_type="collection",
        target_id=name,
        details=details,
    )


# ----------------------------------------------------------------------- #
# Endpoints
# ----------------------------------------------------------------------- #

@router.get("", response_model=list[CollectionAdminOut])
def list_collections_admin(
    admin: User = Depends(_require_manager),
    session: Session = Depends(get_session),
) -> list[CollectionAdminOut]:
    """Alle Sammlungen mit Besitzer, Sichtbarkeit, Mitgliedern (nur Metadaten)."""
    colls = session.exec(select(DocumentCollection).order_by(DocumentCollection.name)).all()
    return [_out(session, c) for c in colls]


@router.post("/{name}/members", response_model=CollectionAdminOut)
def grant_member(
    name: str,
    payload: MemberIn,
    admin: User = Depends(_require_manager),
    session: Session = Depends(get_session),
) -> CollectionAdminOut:
    """Mitglied eintragen oder Stufe aendern. Selbsteintrag = Notfallzugriff."""
    coll = _get_collection(session, name)
    member_user = _get_user_by_email(session, payload.email)
    if member_user.email.lower() == (coll.created_by or "").lower():
        raise HTTPException(400, detail="Dieser User ist bereits Besitzer der Sammlung.")

    member = session.exec(
        select(CollectionMember).where(
            CollectionMember.collection == coll.name,
            CollectionMember.user_id == member_user.id,
        )
    ).first()
    previous = member.level.value if member else None
    if member is None:
        member = CollectionMember(collection=coll.name, user_id=member_user.id, granted_by=admin.email)
    member.level = payload.level
    member.granted_by = admin.email
    session.add(member)
    session.commit()

    _audit(admin, AuditAction.COLLECTION_ACCESS_GRANTED, coll.name, {
        "member": member_user.email,
        "level": payload.level.value,
        "previous_level": previous,
        "emergency_self_grant": member_user.id == admin.id,
    })
    return _out(session, coll)


@router.delete("/{name}/members/{email}", response_model=CollectionAdminOut)
def revoke_member(
    name: str,
    email: str,
    admin: User = Depends(_require_manager),
    session: Session = Depends(get_session),
) -> CollectionAdminOut:
    """Recht entziehen."""
    coll = _get_collection(session, name)
    member_user = _get_user_by_email(session, email)
    member = session.exec(
        select(CollectionMember).where(
            CollectionMember.collection == coll.name,
            CollectionMember.user_id == member_user.id,
        )
    ).first()
    if member is None:
        raise HTTPException(404, detail="Dieser User ist kein Mitglied der Sammlung.")
    level = member.level.value
    session.delete(member)
    session.commit()
    _audit(admin, AuditAction.COLLECTION_ACCESS_REVOKED, coll.name, {
        "member": member_user.email, "level": level,
    })
    return _out(session, coll)


@router.put("/{name}/visibility", response_model=CollectionAdminOut)
def set_visibility(
    name: str,
    payload: VisibilityIn,
    admin: User = Depends(_require_manager),
    session: Session = Depends(get_session),
) -> CollectionAdminOut:
    """'Fuer alle lesbar' an- oder abschalten (z.B. oeffentliche Regulierungstexte)."""
    coll = _get_collection(session, name)
    previous = bool(coll.open_for_all)
    coll.open_for_all = payload.open_for_all
    session.add(coll)
    session.commit()
    _audit(admin, AuditAction.COLLECTION_VISIBILITY_CHANGED, coll.name, {
        "open_for_all": payload.open_for_all, "previous": previous,
    })
    return _out(session, coll)


@router.put("/{name}/owner", response_model=CollectionAdminOut)
def transfer_owner(
    name: str,
    payload: OwnerIn,
    admin: User = Depends(_require_manager),
    session: Session = Depends(get_session),
) -> CollectionAdminOut:
    """Besitz uebertragen, z.B. bei verwaister Sammlung (User geloescht/deaktiviert)."""
    coll = _get_collection(session, name)
    new_owner = _get_user_by_email(session, payload.email)
    if not new_owner.is_active:
        raise HTTPException(400, detail="Der neue Besitzer muss ein aktiver User sein.")
    previous = coll.created_by
    coll.created_by = new_owner.email
    session.add(coll)

    # Ein Mitgliedseintrag des neuen Besitzers ist jetzt ueberfluessig
    redundant = session.exec(
        select(CollectionMember).where(
            CollectionMember.collection == coll.name,
            CollectionMember.user_id == new_owner.id,
        )
    ).first()
    if redundant:
        session.delete(redundant)
    session.commit()

    _audit(admin, AuditAction.COLLECTION_OWNER_CHANGED, coll.name, {
        "from": previous, "to": new_owner.email,
    })
    return _out(session, coll)
