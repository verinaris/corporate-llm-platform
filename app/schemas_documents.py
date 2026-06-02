"""
API-Schemas für Dokument-Endpoints (Phase 3a–3c).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import Document, DocumentCollection


# ============================================================ #
# Documents
# ============================================================ #

class DocumentOut(BaseModel):
    """Antwort-Repräsentation eines Dokuments."""

    id: int
    collection: str
    original_filename: str
    content_type: str
    size_bytes: int
    page_count: int
    chunk_count: int
    uploaded_by: str
    uploaded_at: datetime

    @classmethod
    def from_document(cls, doc: Document) -> "DocumentOut":
        return cls(
            id=doc.id or 0,
            collection=doc.collection,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            uploaded_by=doc.uploaded_by,
            uploaded_at=doc.uploaded_at,
        )


# ============================================================ #
# Collections (Phase 3c)
# ============================================================ #

class CollectionInfo(BaseModel):
    """Metadaten einer Sammlung (Beschreibung + Tags)."""

    name: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db(cls, c: DocumentCollection) -> "CollectionInfo":
        tag_list = [t.strip() for t in (c.tags or "").split(",") if t.strip()]
        return cls(
            name=c.name,
            description=c.description,
            tags=tag_list,
            created_by=c.created_by,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


class CollectionStats(BaseModel):
    """Statistik einer Sammlung (kombiniert Info + Zahlen)."""

    name: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    document_count: int = 0
    chunk_count: int = 0
    total_size_bytes: int = 0


class CollectionUpdate(BaseModel):
    """Eingabe für PUT /documents/collections/{name}"""

    description: Optional[str] = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)


# ============================================================ #
# Search (Phase 3a)
# ============================================================ #

class SearchHit(BaseModel):
    """Ein Treffer einer Vektor-Suche."""

    chunk_text: str
    document_id: int
    document_filename: str
    page: int
    distance: float = Field(
        description="Kleinerer Wert = ähnlicher (0.0 = identisch)"
    )


class SearchResponse(BaseModel):
    """Antwort einer Vektor-Suche."""

    query: str
    collection: str
    hits: list[SearchHit]
