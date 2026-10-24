"""Tests: Datenmodell fuer Archiv, Aufbewahrung und Loeschnachweis (A1)."""

from sqlmodel import Session, SQLModel, create_engine

from app.auth.permissions import can_manage_retention
from app.branches.profiles import get_industry_profile
from app.models import DeletionRecord, Document, DocumentCollection, UserBranch


def test_neue_sammlung_ist_unbekannt_und_ohne_sperre():
    c = DocumentCollection(name="akte", created_by="a@x.de")
    assert c.archived_at is None and c.retain_until is None
    assert c.legal_hold is False


def test_dokument_nicht_archiviert():
    d = Document(collection="akte", original_filename="x.pdf", uploaded_by="a@x.de")
    assert d.archived_at is None


def test_loeschnachweis_speicherbar():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        r = DeletionRecord(collection="akte", document_count=2, requested_by="c@x.de")
        s.add(r)
        s.commit()
        s.refresh(r)
        assert r.id and r.deleted_at and r.content_hashes == "[]"


def test_wer_fristen_setzen_darf():
    assert can_manage_retention("admin") and can_manage_retention("compliance-officer")
    for rolle in ("qualified-reviewer", "user"):
        assert not can_manage_retention(rolle)


def test_branchen_vorgabe_unbekannt():
    for b in UserBranch:
        assert get_industry_profile(b).default_retention_years is None
