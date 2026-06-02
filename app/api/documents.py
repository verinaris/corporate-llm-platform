"""
Documents-API (Phase 3a–3c).

Endpoints:
- POST   /documents                      Upload (PDF) — Admin oder Compliance
- POST   /documents/stream               Upload mit NDJSON-Phasen-Status (3c)
- GET    /documents                      Liste eigener/alle Dokumente
- GET    /documents/{id}                 Einzelnes Dokument (Metadaten)
- GET    /documents/{id}/file            Original-PDF herunterladen (3c)
- DELETE /documents/{id}                 Löschen (DB + ChromaDB + File)
- GET    /documents/collections          Sammlungen + Stats + Beschreibung
- GET    /documents/collections/{name}   Eine Sammlung (Info)
- POST   /documents/collections          Sammlung anlegen mit Beschreibung (3c)
- PUT    /documents/collections/{name}   Beschreibung/Tags ändern (3c)
- GET    /documents/search               Vektor-Suche (für Tests)
"""

import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session, select

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_compliance,
)
from app.database import get_session
from app.models import Document, DocumentCollection, User
from app.schemas_documents import (
    CollectionInfo,
    CollectionStats,
    CollectionUpdate,
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


def _upsert_collection_meta(
    session: Session,
    name: str,
    user_email: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> DocumentCollection:
    """Anlegen oder Updaten der Collection-Metadaten."""
    existing = session.get(DocumentCollection, name)
    if existing:
        if description is not None:
            existing.description = description
        if tags is not None:
            existing.tags = ",".join(t.strip() for t in tags if t.strip())
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    new_coll = DocumentCollection(
        name=name,
        description=description,
        tags=",".join(t.strip() for t in (tags or []) if t.strip()),
        created_by=user_email,
    )
    session.add(new_coll)
    session.commit()
    session.refresh(new_coll)
    return new_coll


# ----------------------------------------------------------------------- #
# Duplikatsprüfung via SHA-256 Hash
# ----------------------------------------------------------------------- #

def _compute_hash(file_bytes: bytes) -> str:
    """SHA-256 Hex-Digest der Datei-Bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def _find_duplicate(
    session: Session,
    collection: str,
    content_hash: str,
) -> Optional[Document]:
    """Sucht in der Sammlung nach einem Dokument mit identischem Hash."""
    return session.exec(
        select(Document).where(
            (Document.collection == collection)
            & (Document.content_hash == content_hash)
        )
    ).first()


def _duplicate_detail_message(existing: Document, collection: str) -> str:
    """Baut die User-Fehlermeldung für ein Duplikat."""
    when = existing.uploaded_at.strftime("%d.%m.%Y")
    return (
        f"Diese Datei ist bereits in der Sammlung '{collection}' vorhanden "
        f"unter dem Namen '{existing.original_filename}' "
        f"(hochgeladen am {when} von {existing.uploaded_by})."
    )


# ----------------------------------------------------------------------- #
# Upload (klassisch — bleibt für Swagger / einfache Clients)
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
    description: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentOut:
    """Lädt ein PDF hoch, zerlegt es und speichert die Embeddings."""
    collection = _validate_collection_name(collection)

    if not (file.content_type or "").startswith("application/pdf"):
        raise HTTPException(
            status_code=400, detail="Nur PDF-Dateien werden unterstützt."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Datei ist leer.")
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß (max. {MAX_UPLOAD_SIZE // (1024 * 1024)} MB).",
        )

    # Duplikatsprüfung (pro Sammlung) — VOR dem aufwändigen PDF-Processing
    content_hash = _compute_hash(file_bytes)
    existing = _find_duplicate(session, collection, content_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=_duplicate_detail_message(existing, collection),
        )

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

    stored_filename = f"{uuid.uuid4().hex}.pdf"
    stored_path = STORAGE_DIR / stored_filename
    stored_path.write_bytes(file_bytes)

    _upsert_collection_meta(
        session=session,
        name=collection,
        user_email=user.email,
        description=description if description else None,
    )

    doc = Document(
        collection=collection,
        original_filename=file.filename or "unbekannt.pdf",
        content_type="application/pdf",
        size_bytes=len(file_bytes),
        page_count=processed.page_count,
        chunk_count=len(processed.chunks),
        uploaded_by=user.email,
        stored_path=str(stored_path),
        content_hash=content_hash,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

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
# Upload mit Phasen-Status (Phase 3c) — NDJSON-Stream
# ----------------------------------------------------------------------- #

@router.post(
    "/stream",
    dependencies=[Depends(require_admin_or_compliance)],
)
async def upload_document_stream(
    file: UploadFile = File(...),
    collection: str = Form(...),
    description: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StreamingResponse:
    """
    Upload mit Phasen-Status (NDJSON-Stream).

    Liefert nacheinander JSON-Zeilen (eine pro Phase):
      {"phase":"upload","status":"done","size_bytes":12345}
      {"phase":"read_pdf","status":"done","pages":12}
      {"phase":"chunk","status":"done","chunks":28}
      {"phase":"embed","status":"start"}
      {"phase":"embed","status":"done"}
      {"phase":"complete","status":"done","document":{...}}

    Bei Fehler:
      {"phase":"error","status":"failed","detail":"..."}

    Streamlit liest die Zeilen und aktualisiert den Phasen-Status live.
    """
    collection_validated = _validate_collection_name(collection)

    if not (file.content_type or "").startswith("application/pdf"):
        raise HTTPException(400, detail="Nur PDF-Dateien werden unterstützt.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(400, detail="Datei ist leer.")
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            413,
            detail=f"Datei zu groß (max. {MAX_UPLOAD_SIZE // (1024 * 1024)} MB).",
        )

    filename = file.filename or "unbekannt.pdf"
    file_size = len(file_bytes)

    async def _generator() -> AsyncGenerator[bytes, None]:

        def event(payload: dict) -> bytes:
            return (json.dumps(payload, default=str) + "\n").encode("utf-8")

        try:
            yield event({
                "phase": "upload",
                "status": "done",
                "size_bytes": file_size,
                "msg": f"Datei empfangen ({file_size / (1024 * 1024):.1f} MB)",
            })

            # Duplikatsprüfung (pro Sammlung)
            content_hash = _compute_hash(file_bytes)
            existing = _find_duplicate(session, collection_validated, content_hash)
            if existing:
                yield event({
                    "phase": "duplicate",
                    "status": "failed",
                    "existing": {
                        "id": existing.id,
                        "filename": existing.original_filename,
                        "uploaded_at": existing.uploaded_at.isoformat(),
                        "uploaded_by": existing.uploaded_by,
                        "collection": collection_validated,
                    },
                    "detail": _duplicate_detail_message(existing, collection_validated),
                })
                return

            yield event({"phase": "read_pdf", "status": "start"})
            t0 = time.perf_counter()
            try:
                processed = process_pdf(file_bytes)
            except Exception as exc:
                yield event({
                    "phase": "error",
                    "status": "failed",
                    "detail": f"PDF konnte nicht gelesen werden: {exc}",
                })
                return

            if not processed.chunks:
                yield event({
                    "phase": "error",
                    "status": "failed",
                    "detail": (
                        "Keine extrahierbaren Texte im PDF "
                        "(evtl. ein Scan? OCR kommt in Phase 3+)"
                    ),
                })
                return

            yield event({
                "phase": "read_pdf",
                "status": "done",
                "pages": processed.page_count,
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            })

            yield event({
                "phase": "chunk",
                "status": "done",
                "chunks": len(processed.chunks),
            })

            stored_filename = f"{uuid.uuid4().hex}.pdf"
            stored_path = STORAGE_DIR / stored_filename
            stored_path.write_bytes(file_bytes)

            _upsert_collection_meta(
                session=session,
                name=collection_validated,
                user_email=user.email,
                description=description if description else None,
            )

            doc = Document(
                collection=collection_validated,
                original_filename=filename,
                content_type="application/pdf",
                size_bytes=file_size,
                page_count=processed.page_count,
                chunk_count=len(processed.chunks),
                uploaded_by=user.email,
                stored_path=str(stored_path),
                content_hash=content_hash,
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)

            yield event({
                "phase": "embed",
                "status": "start",
                "msg": f"Erstelle Embeddings für {len(processed.chunks)} Chunks…",
            })
            t1 = time.perf_counter()

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
                store.add_chunks(collection_validated, ids, texts, metadatas)
            except Exception as exc:
                session.delete(doc)
                session.commit()
                try:
                    stored_path.unlink(missing_ok=True)
                except Exception:
                    pass
                yield event({
                    "phase": "error",
                    "status": "failed",
                    "detail": f"Einbettung fehlgeschlagen: {exc}",
                })
                return

            yield event({
                "phase": "embed",
                "status": "done",
                "elapsed_ms": int((time.perf_counter() - t1) * 1000),
            })

            yield event({
                "phase": "complete",
                "status": "done",
                "document": DocumentOut.from_document(doc).model_dump(mode="json"),
            })

        except Exception as exc:
            yield event({
                "phase": "error",
                "status": "failed",
                "detail": f"Unerwarteter Fehler: {exc}",
            })

    return StreamingResponse(
        _generator(),
        media_type="application/x-ndjson",
    )


# ----------------------------------------------------------------------- #
# Liste / Einzelnes / Löschen
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


# ----------------------------------------------------------------------- #
# Collections-Endpoints (Phase 3c)
# ----------------------------------------------------------------------- #

@router.get("/collections", response_model=list[CollectionStats])
def list_collections(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[CollectionStats]:
    """Alle Sammlungen samt Statistik + Beschreibung."""
    docs = session.exec(select(Document)).all()
    by_coll: dict[str, list[Document]] = {}
    for d in docs:
        by_coll.setdefault(d.collection, []).append(d)

    meta_rows = session.exec(select(DocumentCollection)).all()
    meta_by_name = {m.name: m for m in meta_rows}

    all_names = set(by_coll.keys()) | set(meta_by_name.keys())

    result: list[CollectionStats] = []
    for name in sorted(all_names):
        docs_in_coll = by_coll.get(name, [])
        meta = meta_by_name.get(name)
        tag_list = (
            [t.strip() for t in (meta.tags or "").split(",") if t.strip()]
            if meta else []
        )
        result.append(
            CollectionStats(
                name=name,
                description=meta.description if meta else None,
                tags=tag_list,
                document_count=len(docs_in_coll),
                chunk_count=sum(d.chunk_count for d in docs_in_coll),
                total_size_bytes=sum(d.size_bytes for d in docs_in_coll),
            )
        )
    return result


@router.get("/collections/{name}", response_model=CollectionInfo)
def get_collection(
    name: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CollectionInfo:
    name = _validate_collection_name(name)
    meta = session.get(DocumentCollection, name)
    if not meta:
        return CollectionInfo(name=name)
    return CollectionInfo.from_db(meta)


@router.post(
    "/collections",
    response_model=CollectionInfo,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_or_compliance)],
)
def create_collection(
    name: str = Form(...),
    description: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CollectionInfo:
    """Sammlung manuell anlegen (für leere Sammlungen oder Vorab-Setup)."""
    name = _validate_collection_name(name)
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    meta = _upsert_collection_meta(
        session=session,
        name=name,
        user_email=user.email,
        description=description,
        tags=tag_list,
    )
    return CollectionInfo.from_db(meta)


@router.put(
    "/collections/{name}",
    response_model=CollectionInfo,
    dependencies=[Depends(require_admin_or_compliance)],
)
def update_collection(
    name: str,
    payload: CollectionUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CollectionInfo:
    name = _validate_collection_name(name)
    meta = _upsert_collection_meta(
        session=session,
        name=name,
        user_email=user.email,
        description=payload.description,
        tags=payload.tags,
    )
    return CollectionInfo.from_db(meta)


# ----------------------------------------------------------------------- #
# Search
# ----------------------------------------------------------------------- #

@router.get("/search", response_model=SearchResponse)
def search_documents(
    q: str,
    collection: str,
    limit: int = 5,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SearchResponse:
    """Vektor-Suche in einer Sammlung (Test-Endpoint)."""
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


# ----------------------------------------------------------------------- #
# Einzelnes Dokument + File-Download (Phase 3c)
# ----------------------------------------------------------------------- #

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


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FileResponse:
    """Liefert die Original-PDF zurück (für Vorschau/Download)."""
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(404, detail="Dokument nicht gefunden")
    if not doc.stored_path:
        raise HTTPException(410, detail="Datei nicht mehr verfügbar")
    file_path = Path(doc.stored_path)
    if not file_path.exists():
        raise HTTPException(410, detail="Datei nicht mehr auf dem Server")

    return FileResponse(
        path=str(file_path),
        media_type=doc.content_type or "application/pdf",
        filename=doc.original_filename,
    )


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

    try:
        get_document_store().delete_by_document_id(doc.collection, doc.id or 0)
    except Exception:
        pass

    if doc.stored_path:
        try:
            Path(doc.stored_path).unlink(missing_ok=True)
        except Exception:
            pass

    out = DocumentOut.from_document(doc)
    session.delete(doc)
    session.commit()
    return out
