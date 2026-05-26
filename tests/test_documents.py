"""
Tests für die Documents-API (Phase 3a).

Wir testen primär das Chunking und die Sammlungs-Validierung —
ChromaDB-Integrationstests erfordern das Embedding-Modell und dauern
beim ersten Aufruf länger. Diese laufen daher nur, wenn ENABLE_CHROMA_TESTS=1.
"""

import io
import os

import pytest

from app.services.document_processor import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    _chunk_text,
    _normalize_whitespace,
)


# ============================================================ #
# Whitespace-Normalisierung
# ============================================================ #

def test_normalize_collapses_spaces():
    text = "Das    ist     viel    Whitespace"
    assert _normalize_whitespace(text) == "Das ist viel Whitespace"


def test_normalize_keeps_paragraphs():
    text = "Absatz 1\n\nAbsatz 2"
    out = _normalize_whitespace(text)
    assert "Absatz 1" in out
    assert "Absatz 2" in out


def test_normalize_strips_empty_lines():
    text = "Zeile 1\n   \n\n\nZeile 2"
    out = _normalize_whitespace(text)
    assert out == "Zeile 1\nZeile 2"


# ============================================================ #
# Chunking
# ============================================================ #

def test_chunk_short_text_returns_single_chunk():
    text = "Kurzer Text"
    chunks = _chunk_text(text, chunk_size=800, overlap=120)
    assert chunks == ["Kurzer Text"]


def test_chunk_long_text_is_split():
    text = "A" * 2000
    chunks = _chunk_text(text, chunk_size=800, overlap=120)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 800


def test_chunks_have_overlap():
    text = "ABCDEFGHIJ" * 100  # 1000 Zeichen
    chunks = _chunk_text(text, chunk_size=400, overlap=100)
    assert len(chunks) >= 2
    # Zweiter Chunk sollte mit den letzten 100 Zeichen des ersten beginnen
    overlap_part = chunks[0][-100:]
    assert overlap_part in chunks[1] or chunks[1].startswith(overlap_part[:50])


def test_chunk_defaults_are_sensible():
    assert DEFAULT_CHUNK_SIZE > DEFAULT_CHUNK_OVERLAP
    assert DEFAULT_CHUNK_SIZE > 0
    assert DEFAULT_CHUNK_OVERLAP >= 0


# ============================================================ #
# Sammlungs-Namen-Validierung (über die API)
# ============================================================ #

def test_collection_name_lowercase_ok():
    from app.api.documents import _validate_collection_name
    assert _validate_collection_name("pharma-fachinfos") == "pharma-fachinfos"
    assert _validate_collection_name("HR_Handbuch") == "hr_handbuch"


def test_collection_name_too_short():
    from app.api.documents import _validate_collection_name
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _validate_collection_name("ab")


def test_collection_name_invalid_chars():
    from app.api.documents import _validate_collection_name
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _validate_collection_name("hat leerzeichen")
    with pytest.raises(HTTPException):
        _validate_collection_name("with/slash")


# ============================================================ #
# PDF-Verarbeitung
# ============================================================ #

def test_pdf_processing_with_invalid_bytes_raises():
    """Ein kaputtes PDF wirft eine Exception."""
    from app.services.document_processor import process_pdf

    with pytest.raises(Exception):
        process_pdf(b"This is not a PDF")


def test_pdf_processing_minimal_pdf():
    """Verarbeitet ein minimal-PDF (mit pypdf erstellt)."""
    pypdf = pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    from app.services.document_processor import process_pdf

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)

    result = process_pdf(buf.getvalue())
    # Leere Seite → keine Chunks, page_count = 1
    assert result.page_count == 1
    assert result.chunks == []


# ============================================================ #
# ChromaDB (nur wenn ENABLE_CHROMA_TESTS=1)
# ============================================================ #

CHROMA_ENABLED = os.environ.get("ENABLE_CHROMA_TESTS") == "1"


@pytest.mark.skipif(not CHROMA_ENABLED, reason="Set ENABLE_CHROMA_TESTS=1 to run")
def test_chroma_roundtrip(tmp_path):
    """Chunks rein, Chunks raus."""
    from app.services.document_store import DocumentStore

    store = DocumentStore(persist_path=str(tmp_path / "chroma"))
    store.add_chunks(
        "test-collection",
        ids=["chunk-1", "chunk-2"],
        texts=["Ibuprofen ist ein NSAR.", "Aspirin wirkt entzündungshemmend."],
        metadatas=[
            {"document_id": 1, "page": 1, "filename": "test.pdf"},
            {"document_id": 1, "page": 2, "filename": "test.pdf"},
        ],
    )
    hits = store.query("test-collection", "Schmerzmittel", n_results=2)
    assert len(hits) > 0
    assert "metadata" in hits[0]
