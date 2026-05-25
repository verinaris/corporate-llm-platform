"""
User-Management — nur für Admins.

Endpoints:
- GET    /users        Liste aller User
- POST   /users        User anlegen
- GET    /users/{id}   Einzelnen User holen
- PATCH  /users/{id}   User bearbeiten (Rolle/Branch/aktiv)
- DELETE /users/{id}   User deaktivieren (kein Hard-Delete!)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import require_admin
from app.auth.passwords import hash_password
from app.database import get_session
from app.models import User
from app.schemas_auth import UserCreate, UserOut, UserUpdate

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
    session: Session = Depends(get_session),
) -> UserOut:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    if payload.role is not None:
        user.role = payload.role
    if payload.branch is not None:
        user.branch = payload.branch
    if payload.is_active is not None:
        user.is_active = payload.is_active

    session.add(user)
    session.commit()
    session.refresh(user)
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
