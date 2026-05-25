"""
Pydantic-Schemas für Auth-API.

Getrennt von schemas.py, damit Auth-Konzepte isoliert sind.
"""

from pydantic import BaseModel, EmailStr, Field

from app.models import User, UserBranch, UserRole


class UserOut(BaseModel):
    """User-Repräsentation für API-Antworten (ohne Passwort-Hash!)."""

    id: int
    email: str
    role: UserRole
    branch: UserBranch
    is_active: bool

    @classmethod
    def from_user(cls, user: User) -> "UserOut":
        return cls(
            id=user.id or 0,
            email=user.email,
            role=user.role,
            branch=user.branch,
            is_active=user.is_active,
        )


class LoginResponse(BaseModel):
    """Antwort beim erfolgreichen Login."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    """Eingabe für die Admin-Funktion 'User anlegen'."""

    email: EmailStr
    password: str = Field(min_length=8, description="Mindestens 8 Zeichen")
    role: UserRole = UserRole.USER
    branch: UserBranch = UserBranch.GENERIC


class UserUpdate(BaseModel):
    """Eingabe für die Admin-Funktion 'User bearbeiten'."""

    role: UserRole | None = None
    branch: UserBranch | None = None
    is_active: bool | None = None
