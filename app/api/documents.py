"""
Documents-API (Phase 3a).

Endpoints:
- POST   /documents              Upload (PDF) — Admin oder Compliance-Officer
- GET    /documents              Liste eigener/alle Dokumente
- GET    /documents/{id}         Einzelnes Dokument
- DELETE /documents/{id}         Löschen (DB + ChromaDB)
- GET    /documents/collections  Sammlungen + Stats
- GET    /documents/search       Vektor-Suche (für Tests; Chat-Integration: Phase 3b)
"""

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_compliance,
)
from app.database import get_session
from app.models import Document, User
from app.schemas_documents import (
    CollectionStats,
    DocumentOut,
    SearchHit,
    SearchResponse,
)
from app.services.document_processor import process_pdf
from app.services.document_store import get_document_store

router = APIRouter(prefix="/documents", tags=["documents"])

# Wo die Original-PDFs gespeichert werden (lokal, NICHT in ChromaDB)
STORAGE_DIR = Path("./data/documents")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Max-Upload-Größe in Bytes (200 MB)
MAX_UPLOAD_SIZE = 200 * 1024 * 1024

_COLLECTION_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{1,62}[a-z0-9]$")


def _validate_collection_name(name: str) -> str:
    """ChromaDB ist pingelig: kleinbuchstaben, Bindestriche/Unterstriche ok."""
    name = name.strip().lower()
    if not _COLLECTION_NAME_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=(
                "Ungültiger Sammlungs-Name. Erlaubt: 3-64 Zeichen, "
                "Kleinbuchstaben, Ziffern, '-' oder '_'."
            ),
        )
    return name


# ----------------------------------------------------------------------- #
# Upload
# ----------------------------------------------------------------------- #

@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_or_compliance)],
)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentOut:
    """Lädt ein PDF hoch, zerlegt es und speichert die Embeddings."""
    collection = _validate_collection_name(collection)

    if not (file.content_type or "").startswith("application/pdf"):
        raise HTTPException(
            status_code=400, detail="Nur PDF-Dateien werden unterstützt."
        )

    # Bytes lesen + Größe prüfen
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Datei ist leer.")
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß (max. {MAX_UPLOAD_SIZE // (1024 * 1024)} MB).",
        )

    # PDF verarbeiten
    try:
        processed = process_pdf(file_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"PDF konnte nicht gelesen werden: {exc}",
        ) from exc

    if not processed.chunks:
        raise HTTPException(
            status_code=422,
            detail="Keine extrahierbaren Texte im PDF (evtl. ein Scan? OCR kommt in Phase 3+)",
        )

    # Original-Datei lokal sichern
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    stored_path = STORAGE_DIR / stored_filename
    stored_path.write_bytes(file_bytes)

    # DB-Eintrag
    doc = Document(
        collection=collection,
        original_filename=file.filename or "unbekannt.pdf",
        content_type="application/pdf",
        size_bytes=len(file_bytes),
        page_count=processed.page_count,
        chunk_count=len(processed.chunks),
        uploaded_by=user.email,
        stored_path=str(stored_path),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    # In ChromaDB einfügen
    store = get_document_store()
    ids = [f"doc-{doc.id}-chunk-{c.chunk_index}" for c in processed.chunks]
    texts = [c.text for c in processed.chunks]
    metadatas: list[dict] = [
        {
            "document_id": doc.id,
            "filename": doc.original_filename,
            "page": c.page,
            "chunk_index": c.chunk_index,
            "uploaded_by": user.email,
        }
        for c in processed.chunks
    ]
    try:
        store.add_chunks(collection, ids, texts, metadatas)
    except Exception as exc:
        # Rollback: DB-Eintrag + File entfernen
        session.delete(doc)
        session.commit()
        try:
            stored_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Einbettung fehlgeschlagen: {exc}",
        ) from exc

    return DocumentOut.from_document(doc)


# ----------------------------------------------------------------------- #
# Liste / Einzelnes Dokument / Löschen
# ----------------------------------------------------------------------- #

@router.get("", response_model=list[DocumentOut])
def list_documents(
    collection: str | None = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[DocumentOut]:
    """Alle Dokumente (optional nach Sammlung gefiltert)."""
    query = select(Document)
    if collection:
        query = query.where(Document.collection == _validate_collection_name(collection))
    docs = session.exec(query).all()
    return [DocumentOut.from_document(d) for d in docs]


@router.get("/collections", response_model=list[CollectionStats])
def list_collections(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[CollectionStats]:
    """Alle Sammlungen samt Statistik."""
    docs = session.exec(select(Document)).all()
    by_coll: dict[str, list[Document]] = {}
    for d in docs:
        by_coll.setdefault(d.collection, []).append(d)

    return [
        CollectionStats(
            name=name,
            document_count=len(docs_in_coll),
            chunk_count=sum(d.chunk_count for d in docs_in_coll),
            total_size_bytes=sum(d.size_bytes for d in docs_in_coll),
        )
        for name, docs_in_coll in sorted(by_coll.items())
    ]


@router.get("/search", response_model=SearchResponse)
def search_documents(
    q: str,
    collection: str,
    limit: int = 5,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SearchResponse:
    """Vektor-Suche in einer Sammlung (für Tests; Chat nutzt das später)."""
    collection = _validate_collection_name(collection)
    store = get_document_store()
    raw_hits = store.query(collection, q, n_results=limit)

    hits: list[SearchHit] = []
    for raw in raw_hits:
        meta = raw["metadata"]
        hits.append(
            SearchHit(
                chunk_text=raw["text"],
                document_id=int(meta.get("document_id", 0)),
                document_filename=str(meta.get("filename", "?")),
                page=int(meta.get("page", 0)),
                distance=raw["distance"],
            )
        )
    return SearchResponse(query=q, collection=collection, hits=hits)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentOut:
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(404, detail="Dokument nicht gefunden")
    return DocumentOut.from_document(doc)


@router.delete(
    "/{document_id}",
    response_model=DocumentOut,
    dependencies=[Depends(require_admin_or_compliance)],
)
def delete_document(
    document_id: int,
    session: Session = Depends(get_session),
) -> DocumentOut:
    """Löscht das Dokument: DB-Eintrag, ChromaDB-Chunks, Original-Datei."""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(404, detail="Dokument nicht gefunden")

    # 1. ChromaDB
    try:
        get_document_store().delete_by_document_id(doc.collection, doc.id or 0)
    except Exception:
        pass  # Best effort

    # 2. Originaldatei
    if doc.stored_path:
        try:
            Path(doc.stored_path).unlink(missing_ok=True)
        except Exception:
            pass

    # 3. DB-Eintrag
    out = DocumentOut.from_document(doc)
    session.delete(doc)
    session.commit()
    return out
