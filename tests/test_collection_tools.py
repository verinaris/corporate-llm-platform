"""Tests fuer die Mandantentrennung in den Tools (E3d)."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.database as db
import app.services.collection_access as ca
import app.tools.search_documents as sd
from app.models import DocumentCollection, User, UserRole


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(ca.audit, "log", lambda **kw: None)
    monkeypatch.setattr(sd, "build_rag_context", lambda **kw: ("", []))
    with Session(engine) as s:
        admin = User(email="admin@x.de", password_hash="h", role=UserRole.ADMIN)  # pragma: allowlist secret
        anna = User(email="anna@x.de", password_hash="h")  # pragma: allowlist secret
        s.add_all([admin, anna])
        s.add(DocumentCollection(name="akte-anna", created_by="anna@x.de"))
        s.commit()
        ids = (admin.id, anna.id)
    return engine, ids


def test_suche_ohne_recht_lehnt_klar_ab(env):
    engine, (admin_id, anna_id) = env
    out = sd.SearchDocumentsTool().execute({"query": "x", "collection": "akte-anna"}, user_id=admin_id)
    assert out["error"] == "access_denied"
    assert "Kein Zugriff" in out["summary"]


def test_suche_ohne_user_lehnt_ab(env):
    out = sd.SearchDocumentsTool().execute({"query": "x", "collection": "akte-anna"}, user_id=None)
    assert out["error"] == "access_denied"


def test_suche_als_besitzer_erlaubt(env):
    engine, (admin_id, anna_id) = env
    out = sd.SearchDocumentsTool().execute({"query": "x", "collection": "akte-anna"}, user_id=anna_id)
    assert "error" not in out


def test_import_neue_sammlung_bekommt_besitzer(env):
    engine, (admin_id, anna_id) = env
    assert ca.tool_has_access(admin_id, "ema-neu", "maintain", allow_new=True)
    with Session(engine) as s:
        assert s.get(DocumentCollection, "ema-neu") is None  # generate legt nichts an
    assert ca.tool_claim_upload_target(admin_id, "ema-neu")
    with Session(engine) as s:
        assert s.get(DocumentCollection, "ema-neu").created_by == "admin@x.de"


def test_import_in_fremde_sammlung_abgelehnt(env):
    engine, (admin_id, anna_id) = env
    assert not ca.tool_has_access(admin_id, "akte-anna", "maintain", allow_new=True)
    assert not ca.tool_claim_upload_target(admin_id, "akte-anna")
