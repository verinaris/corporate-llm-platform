"""
FastAPI-Dependencies für Authentifizierung.

Stellt drei Funktionen bereit, die Endpoints als Dependency nutzen können:
- get_current_user      → User aus Token holen (muss eingeloggt sein)
- require_admin         → ... und muss Admin-Rolle haben
- require_active_user   → ... und muss aktiv sein (Default)
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.auth.jwt import decode_access_token
from app.database import get_session
from app.models import User, UserRole

# tokenUrl zeigt auf den Login-Endpoint (wird in Swagger-UI verlinkt)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Liefert den User aus dem Bearer-Token. Wirft 401 wenn ungültig."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ungültig oder abgelaufen",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exc
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exc from None

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exc
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Stellt sicher, dass der User Admin-Rechte hat."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin-Rechte erforderlich",
        )
    return user
