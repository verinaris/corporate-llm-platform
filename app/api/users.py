"""
User-Management — nur für Admins.

Endpoints:
- GET    /users        Liste aller User
- POST   /users        User anlegen
- GET    /users/{id}   Einzelnen User holen
- PATCH  /users/{id}   User bearbeiten (Rolle/Branch/aktiv)
- DELETE /users/{id}   User deaktivieren (kein Hard-Delete!)
"""

import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth.dependencies import require_admin
from app.auth.passwords import hash_password
from app.database import get_session
from app.models import AuditAction, User, UserRole
from app.schemas_auth import UserCreate, UserOut, UserUpdate
from app.services import audit

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)



# ----------------------------------------------------------------------- #
# Helfer: Audit mit dem Admin als Handelndem
# ----------------------------------------------------------------------- #

_PW_ALPHABET = string.ascii_letters + string.digits
_PW_LENGTH = 16


def _rv(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _audit_user(request: Request, admin: User, action: AuditAction, target: User,
                details: dict, session: Session) -> None:
    """Handelnder = Admin, Ziel = betroffener User. Niemals Passwoerter loggen."""
    audit.log(
        user_email=admin.email,
        action=action,
        user_role=_rv(admin.role),
        target_type="user",
        target_id=str(target.id),
        details={"user": target.email, **details},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        session=session,
    )


def _no_self_lockout(admin: User, target: User, payload_role=None, deactivate=False) -> None:
    """Ein Admin darf sich nicht selbst aussperren (Ein-Admin-Kunden!)."""
    if target.id != admin.id:
        return
    if deactivate:
        raise HTTPException(400, detail="Sie können sich nicht selbst deaktivieren.")
    if payload_role is not None and payload_role != UserRole.ADMIN:
        raise HTTPException(400, detail="Sie können sich nicht selbst die Admin-Rolle entziehen.")


class PasswordResetOut(BaseModel):
    user: UserOut
    temporary_password: str


@router.get("", response_model=list[UserOut])
def list_users(session: Session = Depends(get_session)) -> list[UserOut]:
    users = session.exec(select(User)).all()
    return [UserOut.from_user(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UserOut:
    existing = session.exec(
        select(User).where(User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-Mail ist bereits vergeben",
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        branch=payload.branch,
        must_change_password=True,  # Erstpasswort muss beim ersten Login geaendert werden
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    _audit_user(request, admin, AuditAction.USER_CREATED, user,
                {"role": _rv(user.role), "branch": _rv(user.branch)}, session)
    return UserOut.from_user(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
) -> UserOut:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")
    return UserOut.from_user(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UserOut:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")
    _no_self_lockout(admin, user, payload_role=payload.role,
                     deactivate=payload.is_active is False)

    old_branch = _rv(user.branch)
    old_role = _rv(user.role)
    old_active = bool(user.is_active)
    branch_changed = payload.branch is not None and payload.branch != user.branch

    if payload.role is not None:
        user.role = payload.role
    if payload.branch is not None:
        user.branch = payload.branch
    if payload.is_active is not None:
        user.is_active = payload.is_active

    session.add(user)
    session.commit()
    session.refresh(user)

    # Branchenwechsel durch Admin (bewusst unveraendert: Handelnder ist hier
    # historisch der betroffene User, 'by': 'admin' kennzeichnet den Admin).
    if branch_changed:
        audit.log(
            user_email=user.email,
            action=AuditAction.BRANCH_CHANGED,
            user_role=_rv(user.role),
            target_type="user",
            target_id=str(user.id),
            details={"from": old_branch, "to": _rv(user.branch), "by": "admin"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            session=session,
        )

    # Rollen- und Aktiv-Aenderungen: Handelnder ist der Admin
    if _rv(user.role) != old_role:
        _audit_user(request, admin, AuditAction.USER_UPDATED, user,
                    {"field": "role", "from": old_role, "to": _rv(user.role)}, session)
    if bool(user.is_active) != old_active:
        _audit_user(request, admin, AuditAction.USER_UPDATED, user,
                    {"field": "is_active", "from": old_active, "to": bool(user.is_active)}, session)

    return UserOut.from_user(user)


@router.delete("/{user_id}", response_model=UserOut)
def deactivate_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UserOut:
    """
    Deaktivieren statt löschen (soft delete).
    User-Daten bleiben in der DB für Audit-Zwecke.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")
    _no_self_lockout(admin, user, deactivate=True)
    was_active = bool(user.is_active)
    user.is_active = False
    session.add(user)
    session.commit()
    session.refresh(user)
    if was_active:
        _audit_user(request, admin, AuditAction.USER_DELETED, user, {"soft": True}, session)
    return UserOut.from_user(user)


@router.post("/{user_id}/reset-password", response_model=PasswordResetOut)
def reset_password(
    user_id: int,
    request: Request,
    response: Response,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> PasswordResetOut:
    """
    Setzt ein neues Zufalls-Erstpasswort (Aenderungszwang beim naechsten Login).

    Das Passwort steht GENAU EINMAL in dieser Antwort und nirgends sonst,
    nicht im Audit, nicht im Log. Das eigene Passwort aendert der Admin
    ueber 'Passwort ändern'.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(400, detail="Ihr eigenes Passwort ändern Sie über 'Passwort ändern'.")
    if not user.is_active:
        raise HTTPException(400, detail="Bitte den User zuerst reaktivieren.")

    temp = "".join(secrets.choice(_PW_ALPHABET) for _ in range(_PW_LENGTH))
    user.password_hash = hash_password(temp)
    user.must_change_password = True
    session.add(user)
    session.commit()
    session.refresh(user)

    _audit_user(request, admin, AuditAction.PASSWORD_RESET_BY_ADMIN, user, {}, session)
    response.headers["Cache-Control"] = "no-store"
    return PasswordResetOut(user=UserOut.from_user(user), temporary_password=temp)
