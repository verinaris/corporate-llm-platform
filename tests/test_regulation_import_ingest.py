"""Tests: Regulierungs-Import legt echte Dokumente ab (gemeinsamer Ablage-Weg)."""

import asyncio

import pytest
from sqlmodel import Session, select

import app.api.documents as docs_api
import app.services.text_ingest as ti
import app.tools.regulation_import as ri
from app.database import engine
from app.models import Document, DocumentCollection

TEXT = "§ 1 Anwendungsbereich. Dieses Gesetz gilt für alle Steuern. " * 20


class _FakeStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, collection, ids, texts, metadatas):
        self.added.append((collection, ids, metadatas))


@pytest.fixture
def env(monkeypatch, tmp_path, regular_user):
    store = _FakeStore()
    monkeypatch.setattr(ti, "get_document_store", lambda: store)
    monkeypatch.setattr(docs_api, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(ri, "fetch_clean_text", lambda url: {"text": TEXT, "title": "§ 1 AO"})
    monkeypatch.setattr(ri, "tool_claim_upload_target", lambda uid, coll: True)
    yield store, regular_user
    with Session(engine) as s:
        for d in s.exec(select(Document).where(Document.collection == "test-import")).all():
            s.delete(d)
        c = s.get(DocumentCollection, "test-import")
        if c:
            s.delete(c)
        s.commit()


def _run(user_id):
    return asyncio.run(ri.RegulationImportTool().execute(
        {"url": "https://example.org/ao/1", "collection": "test-import"}, user_id=user_id))


def test_import_legt_dokument_an(env):
    store, user = env
    out = _run(user.id)
    assert out["ok"] is True and out["document_id"]
    with Session(engine) as s:
        doc = s.get(Document, out["document_id"])
        assert doc.collection == "test-import"
        assert doc.uploaded_by == user.email
        assert doc.original_filename == "§ 1 AO"
        assert doc.chunk_count == out["chunks"] > 0
    _, ids, metas = store.added[0]
    assert ids[0].startswith(f"doc-{doc.id}-chunk-")
    assert metas[0]["source"] == "https://example.org/ao/1"


def test_zweiter_import_ist_duplikat(env):
    store, user = env
    assert _run(user.id)["ok"] is True
    out = _run(user.id)
    assert out["ok"] is False and "bereits" in out["error"]
    assert len(store.added) == 1


def test_ohne_antragsteller_kein_import(env):
    assert _run(None)["ok"] is False
