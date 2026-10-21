"""Tests fuer den Tuersteher der Mandantentrennung (E3a)."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

import app.services.collection_access as ca
from app.models import (
    AuditAction,
    CollectionAccessLevel,
    CollectionMember,
    DocumentCollection,
    User,
    UserRole,
)


@pytest.fixture
def env(monkeypatch):
    logged = []
    monkeypatch.setattr(ca.audit, "log", lambda **kw: logged.append(kw))
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    s = Session(engine)
    admin = User(email="admin@x.de", password_hash="h", role=UserRole.ADMIN)  # pragma: allowlist secret
    anna = User(email="anna@x.de", password_hash="h")  # pragma: allowlist secret
    bert = User(email="bert@x.de", password_hash="h")  # pragma: allowlist secret
    s.add_all([admin, anna, bert])
    s.add(DocumentCollection(name="akte-anna", created_by="anna@x.de"))
    s.commit()
    s.add(CollectionMember(collection="akte-anna", user_id=bert.id, granted_by="admin@x.de"))
    s.commit()
    return s, admin, anna, bert, logged


def test_admin_bekommt_403_und_audit(env):
    s, admin, anna, bert, logged = env
    with pytest.raises(HTTPException) as exc:
        ca.require_collection_access(s, admin, "akte-anna")
    assert exc.value.status_code == 403
    assert logged and logged[0]["action"] == AuditAction.COLLECTION_ACCESS_DENIED
    assert logged[0]["target_id"] == "akte-anna"


def test_gleiche_meldung_fuer_unbekannt_und_gesperrt(env):
    s, admin, anna, bert, logged = env
    with pytest.raises(HTTPException) as a:
        ca.require_collection_access(s, admin, "akte-anna")
    with pytest.raises(HTTPException) as b:
        ca.require_collection_access(s, admin, "gibt-es-nicht")
    assert a.value.detail.replace("akte-anna", "X") == b.value.detail.replace("gibt-es-nicht", "X")


def test_leser_darf_lesen_aber_nicht_pflegen(env):
    s, admin, anna, bert, logged = env
    assert ca.require_collection_access(s, bert, "akte-anna") == "read"
    with pytest.raises(HTTPException):
        ca.require_collection_access(s, bert, "akte-anna", need="maintain")


def test_upload_neue_sammlung_erlaubt_bestehende_nur_mit_pflege(env):
    s, admin, anna, bert, logged = env
    assert ca.require_upload_target(s, bert, "neue-sammlung") == "new"
    assert ca.require_upload_target(s, anna, "akte-anna") == "owner"
    with pytest.raises(HTTPException):
        ca.require_upload_target(s, bert, "akte-anna")


def test_tool_variante_ohne_user_lehnt_ab(env):
    s, admin, anna, bert, logged = env
    assert ca.has_collection_access(s, None, "akte-anna") is False
    assert ca.has_collection_access(s, anna.id, "akte-anna") is True
    assert ca.has_collection_access(s, admin.id, "akte-anna") is False
