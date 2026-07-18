"""
Profile-API: User-eigene Plattform-Einstellungen.

Aktuell: Branchen-Profil. Künftig: weitere Personalisierungen (Sprache, Theme, ...).

Trennung von `/users` (Admin-only User-Verwaltung) bewusst: Hier darf jeder
User seine eigenen Settings ändern, ohne Admin-Recht zu brauchen.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.branches.profiles import (
    branch_is_self_assignable,
    IndustryProfile,
    get_industry_profile,
    list_industry_profiles,
)
from app.database import get_session
from app.models import AuditAction, User, UserBranch
from app.services import audit

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
    request: Request,
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

    # Selbstbedienung nur zwischen frei waehlbaren Branchen. Rein in eine
    # regulierte Branche oder raus aus ihr geht nur ueber einen Admin
    # (PATCH /users/{id}) -- sonst waere die Datenresidenz-Policy per
    # Branchenwechsel abwaehlbar.
    current = user.branch.value if hasattr(user.branch, "value") else str(user.branch)
    if not (branch_is_self_assignable(current) and branch_is_self_assignable(new_branch.value)):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=(
                "Diese Branche kann nur ein Admin setzen. "
                "Regulierte Branchen (z.B. Pharma) sind bewusst nicht "
                "selbst waehlbar -- bitte an die Administration wenden."
            ),
        )

    old_branch = user.branch.value if hasattr(user.branch, "value") else str(user.branch)
    user.branch = new_branch
    session.add(user)
    session.commit()
    session.refresh(user)

    audit.log(
        user_email=user.email,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.BRANCH_CHANGED,
        target_type="user", target_id=str(user.id),
        details={"from": old_branch, "to": new_branch.value},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return get_my_profile(user=user)
