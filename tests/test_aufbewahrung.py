"""Tests: Aufbewahrungsfristen, Loeschsperre, Loeschstatus (A3)."""

import uuid
from datetime import date, datetime, timedelta, timezone

from app.models import DocumentCollection
from app.services.retention import purge_status


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _sammlung(client, token):
    name = f"fristtest-{uuid.uuid4().hex[:8]}"
    r = client.post("/documents/collections", data={"name": name}, headers=_h(token))
    assert r.status_code == 201, r.text
    return name


def _eintrag(client, token, name):
    r = client.get("/documents/retention", headers=_h(token))
    assert r.status_code == 200, r.text
    return next(e for e in r.json() if e["name"] == name)


def test_status_reihenfolge():
    heute = date(2026, 10, 24)
    c = DocumentCollection(name="x", created_by="a@x.de")
    assert purge_status(c, heute) == "frist_unbekannt"
    c.retain_until = heute
    assert purge_status(c, heute) == "frist_laeuft"            # bis einschliesslich
    c.retain_until = heute - timedelta(days=1)
    assert purge_status(c, heute) == "nicht_archiviert"
    c.archived_at = datetime.now(timezone.utc)
    assert purge_status(c, heute) == "loeschbar"
    c.legal_hold = True
    assert purge_status(c, heute) == "gesperrt"                # Sperre schlaegt alles


def test_normaler_user_darf_nicht(client, admin_token, user_token):
    name = _sammlung(client, admin_token)
    assert client.get("/documents/retention", headers=_h(user_token)).status_code == 403
    r = client.put(f"/documents/collections/{name}/retention", headers=_h(user_token),
                   json={"retain_until": "2035-12-31", "reason": "Test"})
    assert r.status_code == 403
    r = client.put(f"/documents/collections/{name}/legal-hold", headers=_h(user_token),
                   json={"legal_hold": True, "reason": "Test"})
    assert r.status_code == 403


def test_frist_setzen_und_leeren(client, admin_token):
    name = _sammlung(client, admin_token)
    assert _eintrag(client, admin_token, name)["status"] == "frist_unbekannt"
    r = client.put(f"/documents/collections/{name}/retention", headers=_h(admin_token),
                   json={"retain_until": "2035-12-31", "reason": "HGB § 257, 10 Jahre"})
    assert r.status_code == 200, r.text
    assert r.json()["retain_until"] == "2035-12-31" and r.json()["status"] == "frist_laeuft"
    r = client.put(f"/documents/collections/{name}/retention", headers=_h(admin_token),
                   json={"retain_until": None, "reason": "Frist unklar, Rücksprache Steuerberater"})
    assert r.json()["status"] == "frist_unbekannt"


def test_begruendung_pflicht(client, admin_token):
    name = _sammlung(client, admin_token)
    r = client.put(f"/documents/collections/{name}/retention", headers=_h(admin_token),
                   json={"retain_until": "2035-12-31", "reason": "  "})
    assert r.status_code == 422
    r = client.put(f"/documents/collections/{name}/legal-hold", headers=_h(admin_token),
                   json={"legal_hold": True})
    assert r.status_code == 422


def test_loeschsperre(client, admin_token):
    name = _sammlung(client, admin_token)
    r = client.put(f"/documents/collections/{name}/legal-hold", headers=_h(admin_token),
                   json={"legal_hold": True, "reason": "Behördliche Prüfung 2026"})
    assert r.status_code == 200, r.text
    e = _eintrag(client, admin_token, name)
    assert e["status"] == "gesperrt" and e["legal_hold_reason"] == "Behördliche Prüfung 2026"
    r = client.put(f"/documents/collections/{name}/legal-hold", headers=_h(admin_token),
                   json={"legal_hold": False, "reason": "Prüfung abgeschlossen"})
    e = r.json()
    assert e["legal_hold"] is False and e["legal_hold_reason"] is None


def test_unbekannte_sammlung(client, admin_token):
    r = client.put("/documents/collections/gibt-es-nicht-xyz/retention", headers=_h(admin_token),
                   json={"retain_until": None, "reason": "Test"})
    assert r.status_code == 404
