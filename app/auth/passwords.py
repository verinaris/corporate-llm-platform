"""
Passwort-Hashing mit bcrypt.

NIEMALS Passwörter im Klartext speichern! bcrypt erzeugt einen Hash mit
eingebautem Salt — selbst identische Passwörter ergeben verschiedene Hashes.

Analogie: Wie ein Fingerabdruck. Aus dem Abdruck kann man das Originalfinger
nicht rekonstruieren, aber jeder Finger gibt zuverlässig denselben Abdruck.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Erzeugt einen bcrypt-Hash für ein Passwort."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Prüft, ob ein Passwort zu einem Hash passt."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
