"""
API-Schemas für Dokument-Endpoints (Phase 3a).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Document


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


class CollectionStats(BaseModel):
    """Statistik einer Sammlung."""

    name: str
    document_count: int
    chunk_count: int
    total_size_bytes: int


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
