"""Tests: Archivieren und Wiederherstellen von Dokumenten und Sammlungen (A2)."""

import uuid

import pytest

from app.services import archive as archive_svc
from app.services import text_ingest


class FakeStore:
    """Attrappe des Suchindex: merkt sich nur, welche Textstuecke drin sind."""

    def __init__(self):
        self.chunks: dict = {}
        self.fail_delete = False

    def add_chunks(self, coll, ids, texts, metadatas):
        for i, m in zip(ids, metadatas):
            self.chunks[(coll, i)] = m

    def delete_by_document_id(self, coll, document_id):
        if self.fail_delete:
            raise RuntimeError("Index nicht erreichbar")
        weg = [k for k, m in self.chunks.items() if k[0] == coll and m["document_id"] == document_id]
        for k in weg:
            del self.chunks[k]
        return len(weg)

    def anzahl(self, coll, document_id):
        return sum(1 for k, m in self.chunks.items() if k[0] == coll and m["document_id"] == document_id)


@pytest.fixture
def store(monkeypatch):
    s = FakeStore()
    monkeypatch.setattr(text_ingest, "get_document_store", lambda: s)
    monkeypatch.setattr(archive_svc, "get_document_store", lambda: s)
    return s


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _sammlung():
    return f"archivtest-{uuid.uuid4().hex[:8]}"


def _text(client, token, coll, text=None):
    text = text or ("Archivtest " + uuid.uuid4().hex + ". " + "Inhalt der Notiz. " * 40)
    r = client.post("/documents/text", headers=_h(token),
                    json={"title": "Notiz", "text": text, "collection": coll})
    return r


def _ids(client, token, coll):
    r = client.get(f"/documents?collection={coll}", headers=_h(token))
    assert r.status_code == 200, r.text
    return [d["id"] for d in r.json()]


def test_dokument_archivieren_und_wiederherstellen(client, admin_token, store):
    coll = _sammlung()
    r = _text(client, admin_token, coll)
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    assert store.anzahl(coll, doc_id) > 0

    r = client.delete(f"/documents/{doc_id}", headers=_h(admin_token))
    assert r.status_code == 200, r.text
    assert store.anzahl(coll, doc_id) == 0                      # raus aus der Suche
    assert doc_id not in _ids(client, admin_token, coll)        # raus aus der Liste
    assert client.get(f"/documents/{doc_id}", headers=_h(admin_token)).status_code == 404
    assert client.delete(f"/documents/{doc_id}", headers=_h(admin_token)).status_code == 404

    arch = client.get("/documents/archive", headers=_h(admin_token)).json()
    eintrag = [d for d in arch["documents"] if d["id"] == doc_id]
    assert eintrag and eintrag[0]["can_restore"] is True

    r = client.post(f"/documents/{doc_id}/restore", headers=_h(admin_token))
    assert r.status_code == 200, r.text
    assert store.anzahl(coll, doc_id) > 0                       # neu eingelesen
    assert doc_id in _ids(client, admin_token, coll)
    assert client.post(f"/documents/{doc_id}/restore", headers=_h(admin_token)).status_code == 409


def test_indexfehler_archiviert_nicht(client, admin_token, store):
    coll = _sammlung()
    doc_id = _text(client, admin_token, coll).json()["id"]
    store.fail_delete = True
    r = client.delete(f"/documents/{doc_id}", headers=_h(admin_token))
    assert r.status_code == 500
    assert "NICHT archiviert" in r.json()["detail"]
    assert doc_id in _ids(client, admin_token, coll)


def test_duplikat_im_archiv_wird_benannt(client, admin_token, store):
    coll = _sammlung()
    text = "Dublette " + uuid.uuid4().hex + ". " + "Gleicher Inhalt. " * 40
    doc_id = _text(client, admin_token, coll, text).json()["id"]
    client.delete(f"/documents/{doc_id}", headers=_h(admin_token))
    r = _text(client, admin_token, coll, text)
    assert r.status_code == 409
    assert "Archiv" in r.json()["detail"]


def test_sammlung_archivieren_sperrt_alles(client, admin_token, store):
    coll = _sammlung()
    doc_id = _text(client, admin_token, coll).json()["id"]

    r = client.post(f"/documents/collections/{coll}/archive", headers=_h(admin_token))
    assert r.status_code == 200, r.text
    namen = [c["name"] for c in client.get("/documents/collections", headers=_h(admin_token)).json()]
    assert coll not in namen
    assert client.get(f"/documents/collections/{coll}", headers=_h(admin_token)).status_code == 403
    assert client.get(f"/documents/search?q=x&collection={coll}", headers=_h(admin_token)).status_code == 403
    assert client.get(f"/documents/{doc_id}", headers=_h(admin_token)).status_code == 404
    r = _text(client, admin_token, coll)
    assert r.status_code == 409 and "archiviert" in r.json()["detail"]
    assert client.post(f"/documents/collections/{coll}/archive", headers=_h(admin_token)).status_code == 403

    arch = client.get("/documents/archive", headers=_h(admin_token)).json()
    eintrag = [c for c in arch["collections"] if c["name"] == coll]
    assert eintrag and eintrag[0]["document_count"] == 1 and eintrag[0]["legal_hold"] is False

    r = client.post(f"/documents/collections/{coll}/restore", headers=_h(admin_token))
    assert r.status_code == 200, r.text
    namen = [c["name"] for c in client.get("/documents/collections", headers=_h(admin_token)).json()]
    assert coll in namen
    assert client.post(f"/documents/collections/{coll}/restore", headers=_h(admin_token)).status_code == 409


def test_fremde_sehen_archiv_nicht(client, admin_token, user_token, store):
    coll = _sammlung()
    doc_id = _text(client, admin_token, coll).json()["id"]
    client.delete(f"/documents/{doc_id}", headers=_h(admin_token))
    arch = client.get("/documents/archive", headers=_h(user_token)).json()
    assert doc_id not in [d["id"] for d in arch["documents"]]
    assert client.post(f"/documents/{doc_id}/restore", headers=_h(user_token)).status_code in (403, 404)


def test_normaler_user_darf_nicht_archivieren(client, admin_token, user_token, store):
    coll = _sammlung()
    doc_id = _text(client, admin_token, coll).json()["id"]
    assert client.delete(f"/documents/{doc_id}", headers=_h(user_token)).status_code in (403, 404)
    assert client.post(f"/documents/collections/{coll}/archive", headers=_h(user_token)).status_code in (403, 404)
    assert doc_id in _ids(client, admin_token, coll)
