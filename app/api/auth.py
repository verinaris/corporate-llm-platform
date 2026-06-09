"""
Auth-Endpoints: Login + Me.

Login folgt OAuth2-Password-Flow, weil das die Swagger-UI-Integration
in FastAPI nahtlos macht (Authorize-Button funktioniert direkt).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.passwords import verify_password
from app.database import get_session
from app.models import AuditAction, User
from app.schemas_auth import LoginResponse, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> LoginResponse:
    """
    Login via E-Mail + Passwort.

    OAuth2PasswordRequestForm liefert `username` und `password` —
    wir verwenden das `username`-Feld als E-Mail.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        audit.log(
            user_email=form_data.username,
            action=AuditAction.LOGIN_FAILED,
            ip_address=ip, user_agent=ua, success=False,
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falsche E-Mail oder Passwort",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        audit.log(
            user_email=user.email,
            user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
            action=AuditAction.LOGIN_FAILED,
            ip_address=ip, user_agent=ua, success=False,
            details={"reason": "account_inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account ist deaktiviert",
        )

    token = create_access_token(user_id=user.id or 0, email=user.email)
    audit.log(
        user_email=user.email,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.LOGIN,
        ip_address=ip, user_agent=ua,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.from_user(user),
    )


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> UserOut:
    """Gibt Infos zum gerade eingeloggten User zurück."""
    return UserOut.from_user(current)
