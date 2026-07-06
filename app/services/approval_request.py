"""
ApprovalRequestService — Verwaltung offener Vier-Augen-Antraege.

Wenn ein User ein sensitives Tool aufrufen will, wird hier ein PendingApproval
erstellt. Compliance-Officer sieht diese im Dashboard und kann sie freigeben
oder ablehnen.

Bei Freigabe wird automatisch ein ApprovalToken generiert (via approval.py).

Analogie: Poststelle, die Antraege sammelt und an den Compliance-Officer
weiterleitet.
"""

import json
from datetime import datetime

from sqlmodel import Session, select

from app.database import get_session
from app.models import ApprovalStatus, PendingApproval
from app.services.approval import _hash_params, create_token


def create_request(
    requester_email: str,
    requester_role: str,
    tool_name: str,
    params: dict,
    reason: str | None = None,
) -> PendingApproval:
    """
    User stellt Antrag auf Tool-Ausfuehrung.

    Analogie: Zettel in den Briefkasten des Compliance-Officers werfen.
    """
    request = PendingApproval(
        requester_email=requester_email,
        requester_role=requester_role,
        tool_name=tool_name,
        params_json=json.dumps(params, ensure_ascii=False, sort_keys=True),
        params_hash=_hash_params(params),
        reason=reason,
        status=ApprovalStatus.PENDING,
    )

    with next(get_session()) as session:
        session.add(request)
        session.commit()
        session.refresh(request)

    return request


def list_pending() -> list[PendingApproval]:
    """
    Zeigt alle offenen Antraege fuer das Compliance-Dashboard.

    Analogie: Blick in den Posteingang.
    """
    with next(get_session()) as session:
        stmt = (
            select(PendingApproval)
            .where(PendingApproval.status == ApprovalStatus.PENDING)
            .order_by(PendingApproval.created_at)
        )
        return list(session.exec(stmt))


def approve_request(
    request_id: int,
    approver_email: str,
    approver_role: str,
    decision_notes: str | None = None,
) -> tuple[PendingApproval, str]:
    """
    Compliance-Officer gibt Antrag frei.

    Erzeugt automatisch einen Approval-Token (15 Min gueltig, einmal nutzbar).

    Returns:
        (aktualisierter PendingApproval, Token-String)

    Analogie: Anfrage mit Stempel versehen und Ticket ausstellen.
    """
    with next(get_session()) as session:
        request = session.get(PendingApproval, request_id)
        if not request:
            raise ValueError(f"Request {request_id} nicht gefunden")
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request {request_id} bereits entschieden ({request.status})"
            )

        # Params aus JSON zurueckholen
        params = json.loads(request.params_json)

        # Token ausstellen
        token = create_token(
            requester_email=request.requester_email,
            requester_role=request.requester_role,
            tool_name=request.tool_name,
            params=params,
            approver_email=approver_email,
            approver_role=approver_role,
        )

        # Request aktualisieren
        request.status = ApprovalStatus.APPROVED
        request.decided_by_email = approver_email
        request.decided_by_role = approver_role
        request.decision_notes = decision_notes
        request.decided_at = datetime.utcnow()
        request.approval_token = token.token

        session.add(request)
        session.commit()
        session.refresh(request)

    return request, token.token


def reject_request(
    request_id: int,
    approver_email: str,
    approver_role: str,
    decision_notes: str,
) -> PendingApproval:
    """
    Compliance-Officer lehnt Antrag ab.

    decision_notes ist PFLICHT bei Ablehnung (Nachvollziehbarkeit).

    Analogie: Anfrage mit rotem Stempel "Abgelehnt" und Begruendung.
    """
    if not decision_notes or not decision_notes.strip():
        raise ValueError("Ablehnungs-Grund ist Pflicht")

    with next(get_session()) as session:
        request = session.get(PendingApproval, request_id)
        if not request:
            raise ValueError(f"Request {request_id} nicht gefunden")
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request {request_id} bereits entschieden ({request.status})"
            )

        request.status = ApprovalStatus.REJECTED
        request.decided_by_email = approver_email
        request.decided_by_role = approver_role
        request.decision_notes = decision_notes.strip()
        request.decided_at = datetime.utcnow()

        session.add(request)
        session.commit()
        session.refresh(request)

    return request


def get_request(request_id: int) -> PendingApproval | None:
    """Holt einen konkreten Antrag."""
    with next(get_session()) as session:
        return session.get(PendingApproval, request_id)
