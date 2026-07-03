"""
ApprovalService — Vier-Augen-Prinzip für sensitive Tool-Aufrufe.

Ein Compliance-Officer erstellt einen Token für einen konkreten Tool-Call
eines Users. Der Token ist 15 Min gültig und genau einmal verwendbar.

Analogie: Wie ein Kinoticket — kurze Gültigkeit, ein Film, dann entwertet.
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.database import get_session
from app.models import ApprovalToken


TOKEN_TTL_MINUTES = 15  # Gültigkeitsdauer eines Approval-Tokens


def _hash_params(params: dict) -> str:
    """
    Erzeugt einen stabilen SHA256-Hash für Tool-Params.

    Warum? Ein Token soll NUR für exakt diese Params gelten.
    Sortierte Keys → gleicher Hash unabhängig von Dict-Reihenfolge.
    """
    normalized = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def create_token(
    requester_email: str,
    requester_role: str,
    tool_name: str,
    params: dict,
    approver_email: str,
    approver_role: str,
) -> ApprovalToken:
    """
    Compliance-Officer erstellt einen Approval-Token für einen konkreten Call.

    Analogie: Ticket-Ausgabe an der Kinokasse.
    """
    token_str = secrets.token_urlsafe(32)
    now = datetime.utcnow()

    token = ApprovalToken(
        token=token_str,
        requester_email=requester_email,
        requester_role=requester_role,
        tool_name=tool_name,
        params_hash=_hash_params(params),
        approver_email=approver_email,
        approver_role=approver_role,
        created_at=now,
        expires_at=now + timedelta(minutes=TOKEN_TTL_MINUTES),
        used=False,
    )

    with next(get_session()) as session:
        session.add(token)
        session.commit()
        session.refresh(token)

    return token


def consume_token(token_str: str, tool_name: str, params: dict) -> bool:
    """
    Prüft und verbraucht einen Approval-Token.

    Analogie: Ticket-Kontrolle am Kino-Eingang, dann Stempel drauf.

    Returns:
        True wenn Token gültig war und verbraucht wurde
        False wenn Token ungültig, abgelaufen, verbraucht oder Params passen nicht
    """
    now = datetime.utcnow()
    params_hash = _hash_params(params)

    with next(get_session()) as session:
        stmt = select(ApprovalToken).where(ApprovalToken.token == token_str)
        token = session.exec(stmt).first()

        # Prüfungen — alle müssen passen
        if not token:
            return False
        if token.used:
            return False
        if token.expires_at < now:
            return False
        if token.tool_name != tool_name:
            return False
        if token.params_hash != params_hash:
            return False

        # Alles OK → als verbraucht markieren
        token.used = True
        token.used_at = now
        session.add(token)
        session.commit()

    return True
