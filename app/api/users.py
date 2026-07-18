"""
User-Management — nur für Admins.

Endpoints:
- GET    /users        Liste aller User
- POST   /users        User anlegen
- GET    /users/{id}   Einzelnen User holen
- PATCH  /users/{id}   User bearbeiten (Rolle/Branch/aktiv)
- DELETE /users/{id}   User deaktivieren (kein Hard-Delete!)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.auth.dependencies import require_admin
from app.auth.passwords import hash_password
from app.database import get_session
from app.models import AuditAction, User
from app.schemas_auth import UserCreate, UserOut, UserUpdate
from app.services import audit

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[UserOut])
def list_users(session: Session = Depends(get_session)) -> list[UserOut]:
    users = session.exec(select(User)).all()
    return [UserOut.from_user(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
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
    )
    session.add(user)
    session.commit()
    session.refresh(user)
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
    session: Session = Depends(get_session),
) -> UserOut:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    old_branch = (
        user.branch.value if hasattr(user.branch, "value") else str(user.branch)
    )
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

    # Admin verschiebt jemanden ggf. in eine regulierte Branche hinein oder
    # heraus -- das gehoert ins Audit. 'by': 'admin' unterscheidet es vom
    # Selbst-Wechsel in profile.py.
    if branch_changed:
        new_branch = (
            user.branch.value if hasattr(user.branch, "value") else str(user.branch)
        )
        audit.log(
            user_email=user.email,
            action=AuditAction.BRANCH_CHANGED,
            user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
            target_type="user",
            target_id=str(user.id),
            details={"from": old_branch, "to": new_branch, "by": "admin"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            session=session,
        )

    return UserOut.from_user(user)


@router.delete("/{user_id}", response_model=UserOut)
def deactivate_user(
    user_id: int,
    session: Session = Depends(get_session),
) -> UserOut:
    """
    Deaktivieren statt löschen (soft delete).
    User-Daten bleiben in der DB für Audit-Zwecke.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")
    user.is_active = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut.from_user(user)
