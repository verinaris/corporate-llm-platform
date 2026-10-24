"""Tests: endgueltiges Loeschen mit Vier-Augen-Freigabe und Loeschnachweis (A4)."""

import asyncio
import json
import uuid
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.api.approvals import _execute_approved
from app.database import engine
from app.models import DeletionRecord, Document, DocumentCollection
from app.services import archive as archive_svc
from app.services import text_ingest
from app.services.approval_request import approve_request
from app.tools import collection_purge
from app.tools.collection_purge import CollectionPurgeTool
from app.tools.registry import ToolRegistry


class FakeStore:
    def __init__(self):
        self.chunks = {}

    def add_chunks(self, coll, ids, texts, metadatas):
        for i, m in zip(ids, metadatas):
            self.chunks[(coll, i)] = m

    def delete_by_document_id(self, coll, document_id):
        weg = [k for k, m in self.chunks.items() if k[0] == coll and m["document_id"] == document_id]
        for k in weg:
            del self.chunks[k]
        return len(weg)

    def delete_collection(self, coll):
        for k in [k for k in self.chunks if k[0] == coll]:
            del self.chunks[k]

    def anzahl(self, coll):
        return sum(1 for k in self.chunks if k[0] == coll)


@pytest.fixture
def store(monkeypatch):
    s = FakeStore()
    for mod in (text_ingest, archive_svc, collection_purge):
        monkeypatch.setattr(mod, "get_document_store", lambda: s)
    return s


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _sammlung_mit_dokument(client, token):
    name = f"loeschtest-{uuid.uuid4().hex[:8]}"
    r = client.post("/documents/text", headers=_h(token), json={
        "title": "Akte", "collection": name,
        "text": "Akte " + uuid.uuid4().hex + ". " + "Inhalt der Akte. " * 40})
    assert r.status_code == 201, r.text
    return name, r.json()["id"]


def _frist_abgelaufen(client, token, name):
    r = client.put(f"/documents/collections/{name}/retention", headers=_h(token),
                   json={"retain_until": "2020-12-31", "reason": "Frist abgelaufen"})
    assert r.status_code == 200, r.text


def _archivieren(client, token, name):
    assert client.post(f"/documents/collections/{name}/archive", headers=_h(token)).status_code == 200


def _antrag(client, token, name):
    return client.post(f"/documents/collections/{name}/purge-request", headers=_h(token),
                       json={"reason": "Frist abgelaufen, Vernichtung"})


def _freigeben_und_ausfuehren(approval_id):
    req, token = approve_request(approval_id, "freigeber@example.com", "compliance-officer")
    return asyncio.run(_execute_approved(req, token))


def test_endgueltig_loeschen_mit_nachweis(client, admin_token, store):
    name, doc_id = _sammlung_mit_dokument(client, admin_token)
    _frist_abgelaufen(client, admin_token, name)
    _archivieren(client, admin_token, name)
    with Session(engine) as s:
        pfad = Path(s.get(Document, doc_id).stored_path)
    assert pfad.exists() and store.anzahl(name) > 0

    r = _antrag(client, admin_token, name)
    assert r.status_code == 202, r.text
    aid = r.json()["approval_id"]
    with Session(engine) as s:
        assert s.get(DocumentCollection, name) is not None      # vor Freigabe: nichts geloescht

    erg = _freigeben_und_ausfuehren(aid)
    assert erg.execution_status == "succeeded", erg.execution_result
    with Session(engine) as s:
        assert s.get(DocumentCollection, name) is None
        assert s.get(Document, doc_id) is None
        rec = s.exec(select(DeletionRecord).where(DeletionRecord.collection == name)).one()
        assert rec.approved_by == "freigeber@example.com" and rec.approval_id == aid
        assert rec.requested_by == "admin@example.com" and rec.document_count == 1
        assert rec.reason == "Frist abgelaufen, Vernichtung"
        assert len(json.loads(rec.content_hashes)) == 1
    assert not pfad.exists() and store.anzahl(name) == 0

    r = client.get("/documents/deletion-records", headers=_h(admin_token))
    assert r.status_code == 200 and any(e["collection"] == name for e in r.json())


def test_antrag_nur_wenn_loeschbar(client, admin_token, store):
    name, _ = _sammlung_mit_dokument(client, admin_token)
    r = _antrag(client, admin_token, name)                      # Frist unbekannt
    assert r.status_code == 409 and "unbekannt" in r.json()["detail"]
    _frist_abgelaufen(client, admin_token, name)
    r = _antrag(client, admin_token, name)                      # nicht archiviert
    assert r.status_code == 409 and "archiviert" in r.json()["detail"]


def test_sperre_nach_antrag_verhindert_loeschung(client, admin_token, store):
    name, _ = _sammlung_mit_dokument(client, admin_token)
    _frist_abgelaufen(client, admin_token, name)
    _archivieren(client, admin_token, name)
    aid = _antrag(client, admin_token, name).json()["approval_id"]
    client.put(f"/documents/collections/{name}/legal-hold", headers=_h(admin_token),
               json={"legal_hold": True, "reason": "Rechtsstreit"})
    erg = _freigeben_und_ausfuehren(aid)
    assert erg.execution_status == "failed"
    assert "Gesperrt" in erg.execution_result
    with Session(engine) as s:
        assert s.get(DocumentCollection, name) is not None


def test_kein_doppelter_antrag(client, admin_token, store):
    name, _ = _sammlung_mit_dokument(client, admin_token)
    _frist_abgelaufen(client, admin_token, name)
    _archivieren(client, admin_token, name)
    assert _antrag(client, admin_token, name).status_code == 202
    r = _antrag(client, admin_token, name)
    assert r.status_code == 409 and "offener" in r.json()["detail"]


def test_normaler_user_darf_nicht(client, user_token):
    assert client.get("/documents/deletion-records", headers=_h(user_token)).status_code == 403
    r = client.post("/documents/collections/irgendwas/purge-request", headers=_h(user_token),
                    json={"reason": "Test"})
    assert r.status_code == 403


def test_loeschwerkzeug_nicht_fuers_modell():
    if ToolRegistry.get("collection_purge") is None:
        ToolRegistry.register(CollectionPurgeTool())
    for rolle in ("admin", "compliance-officer"):
        assert "collection_purge" not in [t.name for t in ToolRegistry.get_for_role(rolle)]
