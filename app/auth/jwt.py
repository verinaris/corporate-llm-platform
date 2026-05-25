"""
JWT-Token-Generierung und -Verifikation.

JWT = JSON Web Token. Ein signiertes Stück Text, das die App dem Client gibt,
damit er sich bei späteren Requests damit ausweisen kann.

Analogie: Eintrittsband bei einem Konzert. Beim Einlass bekommst du es,
danach zeigst du es nur noch vor — keine erneute Personenkontrolle.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

ALGORITHM = "HS256"


def create_access_token(user_id: int, email: str) -> str:
    """Erzeugt einen JWT für einen User."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),                 # Subject = User-ID
        "email": email,
        "iat": now,                          # Issued at
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Validiert einen JWT und liefert das Payload.

    Wirft `jwt.PyJWTError` bei ungültigem oder abgelaufenem Token.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
