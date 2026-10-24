"""
Aufbewahrung: Fristen, Loeschsperre und Loeschstatus.

Analogie: der Aufkleber auf dem Archivkarton. "Aufbewahren bis 31.12.2035"
oder "Frist unbekannt", dazu ggf. ein roter Aufkleber "Gesperrt" (Legal Hold).
Vernichtet wird nur ein Karton, der im Archiv steht, dessen Frist abgelaufen
ist und der keinen roten Aufkleber hat. Und auch dann nur mit Vier-Augen-Freigabe.
"""

import json
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.auth.permissions import can_manage_retention
from app.models import AuditAction, Document, DocumentCollection, User
from app.services import audit

STATUS_LABELS = {
    "gesperrt": "Gesperrt (Löschsperre)",
    "frist_unbekannt": "Frist unbekannt",
    "frist_laeuft": "Frist läuft",
    "nicht_archiviert": "Nicht archiviert",
    "loeschbar": "Löschbar",
}


def purge_status(coll: DocumentCollection, today: Optional[date] = None) -> str:
    """Staerkstes Hindernis zuerst. Nur 'loeschbar' erlaubt einen Loeschantrag."""
    today = today or date.today()
    if coll.legal_hold:
        return "gesperrt"
    if coll.retain_until is None:
        return "frist_unbekannt"
    if coll.retain_until >= today:          # "bis" einschliesslich
        return "frist_laeuft"
    if coll.archived_at is None:
        return "nicht_archiviert"
    return "loeschbar"


def _role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def require_retention_manager(user: User) -> None:
    if not can_manage_retention(user.role):
        raise HTTPException(403, detail="Nur Compliance-Officer und Administratoren verwalten Aufbewahrungsfristen.")


def get_collection_or_404(session: Session, name: str) -> DocumentCollection:
    coll = session.get(DocumentCollection, name)
    if coll is None:
        raise HTTPException(404, detail=f"Sammlung '{name}' nicht gefunden.")
    return coll


def _reason(reason: str) -> str:
    reason = (reason or "").strip()
    if len(reason) < 3:
        raise HTTPException(422, detail="Bitte eine Begründung angeben (mindestens 3 Zeichen).")
    return reason


def overview_entry(session: Session, coll: DocumentCollection) -> dict:
    """Nur Metadaten, nie Inhalte."""
    docs = session.exec(select(Document).where(Document.collection == coll.name)).all()
    status = purge_status(coll)
    return {
        "name": coll.name, "created_by": coll.created_by,
        "archived_at": coll.archived_at, "retain_until": coll.retain_until,
        "legal_hold": coll.legal_hold, "legal_hold_reason": coll.legal_hold_reason,
        "document_count": len(docs), "size_bytes": sum(d.size_bytes for d in docs),
        "status": status, "status_label": STATUS_LABELS[status],
    }


def overview(session: Session) -> list[dict]:
    colls = session.exec(select(DocumentCollection)).all()
    return [overview_entry(session, c) for c in sorted(colls, key=lambda c: c.name)]


def set_retention(session: Session, coll: DocumentCollection, user: User,
                  retain_until: Optional[date], reason: str) -> DocumentCollection:
    reason = _reason(reason)
    old = coll.retain_until
    coll.retain_until = retain_until
    session.add(coll)
    session.commit()
    session.refresh(coll)
    audit.log(user_email=user.email, user_role=_role(user), action=AuditAction.RETENTION_CHANGED,
              target_type="collection", target_id=coll.name,
              details={"old": old.isoformat() if old else None,
                       "new": retain_until.isoformat() if retain_until else None,
                       "reason": reason})
    return coll


def set_legal_hold(session: Session, coll: DocumentCollection, user: User,
                   hold: bool, reason: str) -> DocumentCollection:
    reason = _reason(reason)
    old = coll.legal_hold
    coll.legal_hold = hold
    coll.legal_hold_reason = reason if hold else None
    session.add(coll)
    session.commit()
    session.refresh(coll)
    audit.log(user_email=user.email, user_role=_role(user), action=AuditAction.LEGAL_HOLD_CHANGED,
              target_type="collection", target_id=coll.name,
              details={"old": old, "new": hold, "reason": reason})
    return coll


# ----------------------------------------------------------------------- #
# Endgueltiges Loeschen: Antrag (Vier-Augen) und Loeschnachweise
# ----------------------------------------------------------------------- #

def request_purge(session: Session, coll: DocumentCollection, user: User, reason: str) -> dict:
    """Legt einen Loeschantrag an. Geloescht wird erst nach Freigabe durch eine andere Person."""
    from app.models import ApprovalStatus, PendingApproval
    from app.tools.collection_purge import TOOL_NAME, CollectionPurgeTool
    from app.tools.registry import ApprovalPendingError, ToolRegistry

    reason = _reason(reason)
    status = purge_status(coll)
    if status != "loeschbar":
        raise HTTPException(409, detail=f"Endgültiges Löschen nicht möglich: {STATUS_LABELS[status]}.")
    offen = session.exec(select(PendingApproval).where(
        PendingApproval.tool_name == TOOL_NAME, PendingApproval.status == ApprovalStatus.PENDING)).all()
    if any(json.loads(r.params_json).get("collection") == coll.name for r in offen):
        raise HTTPException(409, detail="Für diese Sammlung liegt bereits ein offener Löschantrag vor.")

    if ToolRegistry.get(TOOL_NAME) is None:
        ToolRegistry.register(CollectionPurgeTool())
    params = {"collection": coll.name, "requested_at": datetime.now(timezone.utc).isoformat()}
    try:
        ToolRegistry.execute(TOOL_NAME, params, user_id=user.id,
                             user_role=_role(user), user_email=user.email)
    except ApprovalPendingError as pending:
        req = session.get(PendingApproval, pending.request_id)
        req.reason = reason
        session.add(req)
        session.commit()
        return {"approval_id": pending.request_id, "status": "pending", "collection": coll.name}
    raise HTTPException(500, detail="Der Löschantrag konnte nicht angelegt werden.")


def deletion_records(session: Session) -> list[dict]:
    from app.models import DeletionRecord

    rows = session.exec(select(DeletionRecord).order_by(DeletionRecord.deleted_at.desc())).all()
    return [{
        "id": r.id, "object_type": r.object_type, "collection": r.collection,
        "document_count": r.document_count, "chunk_count": r.chunk_count, "size_bytes": r.size_bytes,
        "content_hashes": json.loads(r.content_hashes or "[]"), "retain_until": r.retain_until,
        "requested_by": r.requested_by, "approved_by": r.approved_by, "approval_id": r.approval_id,
        "reason": r.reason, "deleted_at": r.deleted_at,
    } for r in rows]
