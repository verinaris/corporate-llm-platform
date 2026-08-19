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
from app.auth.passwords import verify_password, hash_password
from app.database import get_session
from app.models import AuditAction, User
from app.schemas_auth import LoginResponse, UserOut
from app.services import audit

from pydantic import BaseModel

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

    # Variante B: Testphase startet beim ERSTEN erfolgreichen Login.
    # Danach nie wieder anfassen -- sonst liefe der Countdown neu.
    if user.trial_started_at is None:
        from datetime import datetime, timezone
        user.trial_started_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()

    # Optionaler Passwort-Ablauf (Option B): nur wenn per Settings aktiviert
    # (password_max_age_days > 0). Ist das Passwort aelter als die Frist --
    # oder wurde noch nie ueber die Aender-Funktion gesetzt (kein Zeitstempel)
    # bei aktivierter Richtlinie -- wird ein Wechsel erzwungen. Das Frontend-
    # Gate aus dem Erstpasswort-Zwang greift dann automatisch.
    from app.config import get_settings as _get_settings
    _max_age = _get_settings().password_max_age_days
    if _max_age > 0 and not user.must_change_password:
        from datetime import datetime, timezone, timedelta
        _grenze = datetime.now(timezone.utc) - timedelta(days=_max_age)
        _changed = user.password_changed_at
        # naiv gelesene DB-Zeit als UTC interpretieren (wie bei der Hash-Kette)
        if _changed is not None and _changed.tzinfo is None:
            _changed = _changed.replace(tzinfo=timezone.utc)
        if _changed is None or _changed < _grenze:
            user.must_change_password = True
            session.add(user)
            session.commit()
        session.refresh(user)

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


@router.post("/ack-disclosure", response_model=UserOut)
def acknowledge_disclosure(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserOut:
    """
    Dokumentiert die Bestaetigung des KI-Transparenzhinweises (EU AI Act
    Art. 50). Setzt ai_disclosure_ack_at einmalig und schreibt einen
    Audit-Eintrag. Idempotent: erneute Aufrufe aendern den Zeitstempel nicht.
    """
    from datetime import datetime, timezone

    if user.ai_disclosure_ack_at is None:
        user.ai_disclosure_ack_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        session.refresh(user)

        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        audit.log(
            user_email=user.email,
            user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
            action=AuditAction.AI_DISCLOSURE_ACK,
            ip_address=ip, user_agent=ua,
        )

    return UserOut.from_user(user)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserOut:
    """
    Aendert das Passwort des eingeloggten Users.

    Prueft zwingend das alte Passwort (Schutz gegen gekaperte Sessions),
    setzt das neue als bcrypt-Hash und schreibt einen Audit-Eintrag.
    Das Passwort selbst wird NIE geloggt.
    """
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das aktuelle Passwort ist falsch.",
        )
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das neue Passwort muss mindestens 8 Zeichen lang sein.",
        )
    if payload.new_password == payload.old_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das neue Passwort muss sich vom alten unterscheiden.",
        )

    from datetime import datetime, timezone

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_changed_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit.log(
        user_email=user.email,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.PASSWORD_CHANGED,
        ip_address=ip, user_agent=ua,
    )

    return UserOut.from_user(user)
