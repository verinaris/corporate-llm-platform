"""
CollectionPurgeTool: endgueltiges Loeschen einer ganzen Sammlung.

Analogie: der Aktenvernichter mit zwei Schluesseln. Einer beantragt, ein
anderer gibt frei, und der Vernichter prueft selbst noch einmal den Aufkleber
auf dem Karton (archiviert, Frist abgelaufen, keine Sperre). Zurueck bleibt
nur das Vernichtungsprotokoll (DeletionRecord), nie der Inhalt.

Freigabepflicht unabschaltbar. Nicht fuer das KI-Modell (llm_callable=False):
ein Chat kann keinen Loeschantrag ausloesen.
"""

import json
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.models import (
    ApprovalStatus, AuditAction, CollectionMember, DeletionRecord, Document,
    DocumentCollection, PendingApproval, User,
)
from app.services import audit
from app.services.approval import _hash_params
from app.services.document_store import get_document_store
from app.services.retention import STATUS_LABELS, purge_status
from app.tools.base import BaseTool

TOOL_NAME = "collection_purge"


def _role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _find_approval(session: Session, params: dict):
    """Der freigegebene Antrag zu genau diesen Parametern (fuer Freigeber + Nummer)."""
    return session.exec(
        select(PendingApproval).where(
            PendingApproval.tool_name == TOOL_NAME,
            PendingApproval.params_hash == _hash_params(params),
            PendingApproval.status == ApprovalStatus.APPROVED,
        ).order_by(PendingApproval.id.desc())
    ).first()


class CollectionPurgeTool(BaseTool):
    name = TOOL_NAME
    description = (
        "Löscht eine archivierte Sammlung mit abgelaufener Aufbewahrungsfrist "
        "endgültig (Index, Dateien, Einträge) und schreibt einen Löschnachweis."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "collection": {"type": "string", "description": "Name der Sammlung."},
            "requested_at": {"type": "string", "description": "Zeitpunkt des Antrags (macht ihn eindeutig)."},
        },
        "required": ["collection"],
    }
    requires_human_oversight = True
    allowed_roles = ["admin", "compliance-officer"]
    llm_callable = False

    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        from app.database import engine

        name = (params.get("collection") or "").strip()
        if not name:
            return {"ok": False, "error": "collection ist Pflicht."}

        with Session(engine) as s:
            requester = s.get(User, user_id) if user_id else None
            if requester is None:
                return {"ok": False, "error": "Antragsteller unbekannt."}
            coll = s.get(DocumentCollection, name)
            if coll is None:
                return {"ok": False, "error": f"Die Sammlung '{name}' gibt es nicht (mehr)."}

            # Erneut pruefen: zwischen Antrag und Freigabe kann sich alles geaendert haben
            status = purge_status(coll)
            if status != "loeschbar":
                return {"ok": False, "collection": name,
                        "error": f"Nicht gelöscht, Status jetzt: {STATUS_LABELS[status]}."}

            approval = _find_approval(s, params)
            docs = s.exec(select(Document).where(Document.collection == name)).all()

            store = get_document_store()
            try:
                for d in docs:
                    store.delete_by_document_id(name, d.id or 0)
            except Exception as exc:
                return {"ok": False, "collection": name,
                        "error": f"Suchindex nicht erreichbar, nichts gelöscht: {exc}"}
            store.delete_collection(name)

            files_failed = 0
            for d in docs:
                if d.stored_path:
                    try:
                        Path(d.stored_path).unlink(missing_ok=True)
                    except Exception:
                        files_failed += 1

            record = DeletionRecord(
                object_type="collection",
                collection=name,
                document_count=len(docs),
                chunk_count=sum(d.chunk_count for d in docs),
                size_bytes=sum(d.size_bytes for d in docs),
                content_hashes=json.dumps(sorted(d.content_hash for d in docs if d.content_hash)),
                retain_until=coll.retain_until,
                requested_by=requester.email,
                approved_by=approval.decided_by_email if approval else None,
                approval_id=approval.id if approval else None,
                reason=approval.reason if approval else None,
            )
            s.add(record)
            for d in docs:
                s.delete(d)
            for m in s.exec(select(CollectionMember).where(CollectionMember.collection == name)).all():
                s.delete(m)
            s.delete(coll)
            s.commit()
            s.refresh(record)
            result = {"ok": True, "collection": name, "deletion_record_id": record.id,
                      "documents": record.document_count, "files_failed": files_failed}
            details = {"deletion_record_id": record.id, "documents": record.document_count,
                       "approval_id": record.approval_id, "approved_by": record.approved_by,
                       "files_failed": files_failed}
            requester_email, requester_role = requester.email, _role(requester)

        audit.log(user_email=requester_email, user_role=requester_role,
                  action=AuditAction.COLLECTION_PURGED, target_type="collection",
                  target_id=name, details=details)
        return result
