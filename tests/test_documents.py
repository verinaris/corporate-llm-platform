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


# ============================================================ #
# Collections-API (Phase 3c)
# ============================================================ #

def test_create_collection_as_admin(client, admin_token):
    r = client.post(
        "/documents/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={
            "name": "test-coll-3c",
            "description": "Eine Test-Sammlung für Phase 3c",
            "tags": "pharma, fachinfo, test",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "test-coll-3c"
    assert body["description"] == "Eine Test-Sammlung für Phase 3c"
    assert body["tags"] == ["pharma", "fachinfo", "test"]


def test_create_collection_requires_admin_or_compliance(client, user_token):
    """Normaler User darf KEINE Sammlung anlegen."""
    r = client.post(
        "/documents/collections",
        headers={"Authorization": f"Bearer {user_token}"},
        data={"name": "verboten-coll"},
    )
    assert r.status_code == 403


def test_create_collection_invalid_name(client, admin_token):
    """Sammlungs-Namen müssen Pattern entsprechen."""
    r = client.post(
        "/documents/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"name": "Mit Leerzeichen"},
    )
    assert r.status_code == 400


def test_update_collection(client, admin_token):
    """Erst anlegen, dann description ändern."""
    client.post(
        "/documents/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"name": "update-test", "description": "Original"},
    )
    r = client.put(
        "/documents/collections/update-test",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Neu", "tags": ["a", "b"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["description"] == "Neu"
    assert sorted(body["tags"]) == ["a", "b"]


def test_get_collection_returns_default_for_unknown(client, user_token):
    """Unbekannte Sammlung liefert Default-Info, kein 404."""
    r = client.get(
        "/documents/collections/voellig-neue-sammlung",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "voellig-neue-sammlung"
    assert r.json()["description"] is None


def test_list_collections_includes_description(client, admin_token):
    """Liste enthält description-Feld."""
    client.post(
        "/documents/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"name": "listed-coll", "description": "Erscheint in Liste"},
    )
    r = client.get(
        "/documents/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    found = [c for c in r.json() if c["name"] == "listed-coll"]
    assert len(found) == 1
    assert found[0]["description"] == "Erscheint in Liste"


# ============================================================ #
# File-Download (Phase 3c)
# ============================================================ #

def test_get_document_file_404_for_unknown(client, user_token):
    r = client.get(
        "/documents/99999/file",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 404


# ============================================================ #
# Duplikatsprüfung via SHA-256 Hash
# ============================================================ #

def test_compute_hash_deterministic():
    """Gleiche Bytes → gleicher Hash, immer."""
    from app.api.documents import _compute_hash
    data = b"Hello, World!"
    assert _compute_hash(data) == _compute_hash(data)
    # Bekannter Wert für Hello, World!
    assert _compute_hash(data) == (
        "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    )


def test_compute_hash_different_for_different_bytes():
    from app.api.documents import _compute_hash
    assert _compute_hash(b"a") != _compute_hash(b"b")


def test_duplicate_helpers_with_db(client, admin_token):
    """Smoke-Test: Helper-Funktionen finden Duplikate in der DB."""
    from sqlmodel import Session
    from app.api.documents import _find_duplicate, _compute_hash
    from app.database import engine
    from app.models import Document

    test_hash = _compute_hash(b"test-content-for-dedupe-helper")

    with Session(engine) as session:
        # Kein Duplikat in leerer DB
        assert _find_duplicate(session, "test-coll-dedupe", test_hash) is None

        # Dokument einfügen
        doc = Document(
            collection="test-coll-dedupe",
            original_filename="test.pdf",
            uploaded_by="admin@example.com",
            content_hash=test_hash,
            stored_path="/tmp/fake.pdf",
        )
        session.add(doc)
        session.commit()

        # Jetzt findet er es
        found = _find_duplicate(session, "test-coll-dedupe", test_hash)
        assert found is not None
        assert found.original_filename == "test.pdf"

        # Aber NICHT in einer anderen Sammlung
        not_found = _find_duplicate(session, "andere-coll", test_hash)
        assert not_found is None

        # Aufräumen
        session.delete(doc)
        session.commit()


def test_legacy_doc_without_hash_does_not_block(client, admin_token):
    """Bestehende Dokumente ohne content_hash dürfen Uploads nicht blockieren."""
    from sqlmodel import Session
    from app.api.documents import _find_duplicate
    from app.database import engine
    from app.models import Document

    with Session(engine) as session:
        # Altes Doc OHNE Hash
        legacy = Document(
            collection="test-coll-legacy",
            original_filename="alt.pdf",
            uploaded_by="admin@example.com",
            content_hash=None,
            stored_path="/tmp/fake.pdf",
        )
        session.add(legacy)
        session.commit()

        # Neuer Upload mit irgendeinem Hash darf nicht blockiert werden
        result = _find_duplicate(session, "test-coll-legacy", "irgendein-neuer-hash")
        assert result is None

        # Aufräumen
        session.delete(legacy)
        session.commit()
