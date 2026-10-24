"""
Archiv: das einzige "Loeschen" im Alltag.

Analogie: Die Akte wandert ins Archiv. Die Karteikarten im Suchkasten
(Textstuecke im Suchindex) werden gezogen, die Akte selbst (Originaldatei,
Datenbankeintrag) bleibt erhalten und kann jederzeit zurueckgeholt werden.
Endgueltig vernichtet wird nur ueber die Aufbewahrungsfrist (Vier-Augen).

Dokument: Textstuecke raus aus dem Index, beim Wiederherstellen neu eingelesen.
Sammlung: Index bleibt, die Zugriffspruefung sperrt sie (collection_access).
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session, select

from app.auth.permissions import can_maintain_collection, can_read_collection
from app.models import AuditAction, Document, DocumentCollection, User
from app.services import audit
from app.services.collection_access import get_collection_level
from app.services.document_processor import process_pdf, process_text
from app.services.document_store import get_document_store

_DOC_MANAGERS = frozenset({"admin", "compliance-officer"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _log(user: User, action: AuditAction, target_type: str, target_id: str, details: dict) -> None:
    audit.log(user_email=user.email, user_role=_role(user), action=action,
              target_type=target_type, target_id=target_id, details=details)


def remove_from_index(doc: Document) -> int:
    """Textstuecke aus dem Suchindex entfernen. Fehler werden NICHT verschluckt."""
    return get_document_store().delete_by_document_id(doc.collection, doc.id or 0)


def archive_document(session: Session, doc: Document, user: User) -> Document:
    if doc.archived_at is not None:
        raise HTTPException(409, detail="Das Dokument ist bereits archiviert.")
    try:
        removed = remove_from_index(doc)
    except Exception as exc:
        raise HTTPException(500, detail=(
            "Textstücke konnten nicht aus dem Suchindex entfernt werden, "
            f"das Dokument wurde NICHT archiviert: {exc}")) from exc
    doc.archived_at = _now()
    doc.archived_by = user.email
    session.add(doc)
    session.commit()
    session.refresh(doc)
    _log(user, AuditAction.DOCUMENT_ARCHIVED, "document", str(doc.id),
         {"collection": doc.collection, "filename": doc.original_filename, "chunks_removed": removed})
    return doc


def restore_document(session: Session, doc: Document, user: User) -> Document:
    if doc.archived_at is None:
        raise HTTPException(409, detail="Das Dokument ist nicht archiviert.")
    path = Path(doc.stored_path) if doc.stored_path else None
    if path is None or not path.exists():
        raise HTTPException(410, detail="Die Originaldatei fehlt, Wiederherstellen ist nicht möglich.")
    data = path.read_bytes()
    is_pdf = (doc.content_type or "").startswith("application/pdf")
    processed = process_pdf(data) if is_pdf else process_text(data.decode("utf-8", errors="replace"))
    if not processed.chunks:
        raise HTTPException(422, detail="Aus der Originaldatei ließ sich kein Text lesen.")
    ids = [f"doc-{doc.id}-chunk-{c.chunk_index}" for c in processed.chunks]
    metadatas = []
    for c in processed.chunks:
        m = {"document_id": doc.id, "filename": doc.original_filename, "page": c.page,
             "chunk_index": c.chunk_index, "uploaded_by": doc.uploaded_by}
        if not is_pdf:
            m["source"] = ""
        metadatas.append(m)
    store = get_document_store()
    try:
        store.delete_by_document_id(doc.collection, doc.id or 0)  # Reste weg, keine Dubletten
        store.add_chunks(doc.collection, ids, [c.text for c in processed.chunks], metadatas)
    except Exception as exc:
        raise HTTPException(500, detail=f"Einlesen in den Suchindex fehlgeschlagen: {exc}") from exc
    doc.archived_at = None
    doc.archived_by = None
    doc.chunk_count = len(processed.chunks)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    _log(user, AuditAction.DOCUMENT_RESTORED, "document", str(doc.id),
         {"collection": doc.collection, "filename": doc.original_filename, "chunks": doc.chunk_count})
    return doc


def _doc_count(session: Session, name: str) -> int:
    return len(session.exec(select(Document).where(Document.collection == name)).all())


def archive_collection(session: Session, coll: DocumentCollection, user: User) -> DocumentCollection:
    if coll.archived_at is not None:
        raise HTTPException(409, detail="Die Sammlung ist bereits archiviert.")
    coll.archived_at = _now()
    coll.archived_by = user.email
    session.add(coll)
    session.commit()
    session.refresh(coll)
    _log(user, AuditAction.COLLECTION_ARCHIVED, "collection", coll.name,
         {"documents": _doc_count(session, coll.name)})
    return coll


def restore_collection(session: Session, coll: DocumentCollection, user: User) -> DocumentCollection:
    if coll.archived_at is None:
        raise HTTPException(409, detail="Die Sammlung ist nicht archiviert.")
    coll.archived_at = None
    coll.archived_by = None
    session.add(coll)
    session.commit()
    session.refresh(coll)
    _log(user, AuditAction.COLLECTION_RESTORED, "collection", coll.name,
         {"documents": _doc_count(session, coll.name)})
    return coll


def archive_listing(session: Session, user: User) -> dict:
    """Archivierte Sammlungen und Dokumente, die der User sehen darf (Mandantentrennung)."""
    manager = _role(user) in _DOC_MANAGERS
    sammlungen = []
    for c in session.exec(select(DocumentCollection).where(DocumentCollection.archived_at.is_not(None))).all():
        level = get_collection_level(session, user, c.name, include_archived=True)
        if not can_read_collection(level):
            continue
        docs = session.exec(select(Document).where(Document.collection == c.name)).all()
        sammlungen.append({
            "name": c.name, "description": c.description,
            "archived_at": c.archived_at, "archived_by": c.archived_by,
            "document_count": len(docs), "size_bytes": sum(d.size_bytes for d in docs),
            "retain_until": c.retain_until, "legal_hold": c.legal_hold,
            "can_restore": manager and can_maintain_collection(level),
        })
    dokumente = []
    for d in session.exec(select(Document).where(Document.archived_at.is_not(None))).all():
        level = get_collection_level(session, user, d.collection)  # nur aktive Sammlungen
        if not can_read_collection(level):
            continue
        dokumente.append({
            "id": d.id, "collection": d.collection, "original_filename": d.original_filename,
            "size_bytes": d.size_bytes, "uploaded_by": d.uploaded_by, "uploaded_at": d.uploaded_at,
            "archived_at": d.archived_at, "archived_by": d.archived_by,
            "can_restore": manager and can_maintain_collection(level),
        })
    return {"collections": sammlungen, "documents": dokumente}
