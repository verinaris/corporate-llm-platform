"""
Gemeinsamer Ablage-Weg fuer reinen Text in die Wissensbibliothek.

Genutzt vom Text-Eingang (POST /documents/text) und vom Regulierungs-Import.
Vorher legte der Import seine Textstuecke ohne Dokument-Eintrag ab: unsichtbar
in der Wissensbibliothek, nicht loeschbar, "Original holen" ins Leere, keine
Duplikatspruefung. Jetzt: ein Weg, ein Verhalten.

Analogie: die Poststelle. Egal ob der Brief per Hand oder per Kurier kommt,
er bekommt einen Eingangsstempel, eine Aktennummer und einen Platz im Regal.
"""

import uuid
from typing import Optional

from sqlmodel import Session

from app.models import Document
from app.services.document_processor import process_text
from app.services.document_store import get_document_store


class IngestError(Exception):
    """Fehler mit HTTP-naher Kennung (413, 409, 422, 500) und lesbarer Meldung."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def ingest_text(
    session: Session,
    *,
    user_email: str,
    collection: str,
    title: str,
    text: str,
    source: Optional[str] = None,
    description: Optional[str] = None,
) -> Document:
    """Legt Text als Dokument ab. Rechtepruefung macht der Aufrufer."""
    # spaet importiert: die Helfer leben (noch) im API-Modul
    from app.api import documents as d

    text_bytes = (text or "").encode("utf-8")
    if len(text_bytes) > d.MAX_UPLOAD_SIZE:
        raise IngestError(413, f"Text zu groß (max. {d.MAX_UPLOAD_SIZE // (1024 * 1024)} MB).")

    content_hash = d._compute_hash(text_bytes)
    existing = d._find_duplicate(session, collection, content_hash)
    if existing:
        raise IngestError(409, d._duplicate_detail_message(existing, collection))

    processed = process_text(text)
    if not processed.chunks:
        raise IngestError(422, "Kein verwertbarer Text enthalten.")

    stored_path = d.STORAGE_DIR / f"{uuid.uuid4().hex}.txt"
    stored_path.write_bytes(text_bytes)

    d._upsert_collection_meta(session=session, name=collection, user_email=user_email,
                              description=description or None)

    doc = Document(
        collection=collection,
        original_filename=(title or "Ohne Titel").strip()[:255],
        content_type="text/plain; charset=utf-8",
        size_bytes=len(text_bytes),
        page_count=0,
        chunk_count=len(processed.chunks),
        uploaded_by=user_email,
        stored_path=str(stored_path),
        content_hash=content_hash,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    ids = [f"doc-{doc.id}-chunk-{c.chunk_index}" for c in processed.chunks]
    metadatas = [
        {
            "document_id": doc.id,
            "filename": doc.original_filename,
            "page": c.page,
            "chunk_index": c.chunk_index,
            "uploaded_by": user_email,
            "source": source or "",
        }
        for c in processed.chunks
    ]
    try:
        get_document_store().add_chunks(collection, ids, [c.text for c in processed.chunks], metadatas)
    except Exception as exc:
        session.delete(doc)
        session.commit()
        try:
            stored_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise IngestError(500, f"Einbettung fehlgeschlagen: {exc}") from exc
    return doc
