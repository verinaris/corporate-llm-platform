"""
Profile-API: User-eigene Plattform-Einstellungen.

Aktuell: Branchen-Profil. Künftig: weitere Personalisierungen (Sprache, Theme, ...).

Trennung von `/users` (Admin-only User-Verwaltung) bewusst: Hier darf jeder
User seine eigenen Settings ändern, ohne Admin-Recht zu brauchen.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.branches.profiles import (
    IndustryProfile,
    get_industry_profile,
    list_industry_profiles,
)
from app.database import get_session
from app.models import User, UserBranch

router = APIRouter(prefix="/profile", tags=["profile"])


class IndustryProfileOut(BaseModel):
    """API-Format eines Branchen-Profils."""

    code: str
    name: str
    short_name: str
    icon: str
    description: str
    is_default: bool


class MyProfileOut(BaseModel):
    """Antwort auf GET /profile/me."""

    email: str
    role: str
    branch: str
    branch_profile: IndustryProfileOut


class BranchUpdate(BaseModel):
    """Eingabe für PUT /profile/me/branch."""

    branch: str  # Wert aus UserBranch-Enum


# ============================================================ #
# Endpoints
# ============================================================ #

@router.get("/industries", response_model=list[IndustryProfileOut])
def list_industries() -> list[IndustryProfileOut]:
    """
    Liefert alle verfügbaren Branchen-Profile.

    Öffentlich auflistbar — aber für den Wechsel braucht es Auth.
    """
    return [
        IndustryProfileOut(
            code=p.code,
            name=p.name,
            short_name=p.short_name,
            icon=p.icon,
            description=p.description,
            is_default=p.is_default,
        )
        for p in list_industry_profiles()
    ]


@router.get("/me", response_model=MyProfileOut)
def get_my_profile(
    user: User = Depends(get_current_user),
) -> MyProfileOut:
    """Liefert das Profil des eingeloggten Users (inkl. Branchen-Metadaten)."""
    profile = get_industry_profile(user.branch)
    return MyProfileOut(
        email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        branch=user.branch.value if hasattr(user.branch, "value") else str(user.branch),
        branch_profile=IndustryProfileOut(
            code=profile.code,
            name=profile.name,
            short_name=profile.short_name,
            icon=profile.icon,
            description=profile.description,
            is_default=profile.is_default,
        ),
    )


@router.put("/me/branch", response_model=MyProfileOut)
def update_my_branch(
    payload: BranchUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MyProfileOut:
    """
    Eingeloggter User wechselt sein Branchen-Profil.

    Validiert gegen UserBranch-Enum — unbekannte Codes → 400.
    """
    try:
        new_branch = UserBranch(payload.branch)
    except ValueError:
        valid = [b.value for b in UserBranch]
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Unbekannte Branche '{payload.branch}'. Erlaubt: {valid}",
        )

    user.branch = new_branch
    session.add(user)
    session.commit()
    session.refresh(user)

    return get_my_profile(user=user)
