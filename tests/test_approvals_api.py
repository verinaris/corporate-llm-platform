"""Tests: Vier-Augen-Freigaben ueber die API (F1)."""

from sqlmodel import Session, select

from app.database import engine
from app.models import AuditAction, AuditLog, PendingApproval
from app.services.approval_request import create_request


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _antrag(email="user@example.com", role="user", tool="regulation_import"):
    return create_request(requester_email=email, requester_role=role, tool_name=tool,
                          params={"url": "https://example.org", "collection": "akte-geheim"})


def _cleanup():
    with Session(engine) as s:
        for r in s.exec(select(PendingApproval)).all():
            s.delete(r)
        s.commit()


def test_liste_parameter_nur_fuer_berechtigte(client, admin_token, user_token):
    _cleanup()
    fremd = _antrag(email="dritter@example.com")
    eigen = _antrag(email="user@example.com")
    r = client.get("/approvals", headers=_h(user_token)).json()
    assert r["can_decide"] is False
    by_id = {i["id"]: i for i in r["items"]}
    assert by_id[fremd.id]["params"] is None
    assert by_id[eigen.id]["params"]["collection"] == "akte-geheim"
    r = client.get("/approvals", headers=_h(admin_token)).json()
    assert r["can_decide"] is True
    assert all(i["params"] for i in r["items"])


def test_user_darf_nicht_entscheiden(client, user_token):
    _cleanup()
    a = _antrag(email="dritter@example.com")
    assert client.post(f"/approvals/{a.id}/approve", headers=_h(user_token), json={}).status_code == 403
    with Session(engine) as s:
        assert s.exec(select(AuditLog).where(AuditLog.action == AuditAction.APPROVAL_DENIED)).first()


def test_kein_entscheiden_ueber_eigenen_antrag(client, admin_token):
    _cleanup()
    a = _antrag(email="admin@example.com", role="admin")
    r = client.post(f"/approvals/{a.id}/approve", headers=_h(admin_token), json={})
    assert r.status_code == 403 and "Vier-Augen" in r.json()["detail"]


def test_freigeben_auditiert_und_nur_einmal(client, admin_token):
    _cleanup()
    a = _antrag()
    r = client.post(f"/approvals/{a.id}/approve", headers=_h(admin_token), json={"notes": "ok"})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert r.json()["decided_by_email"] == "admin@example.com"
    with Session(engine) as s:
        assert s.exec(select(AuditLog).where(AuditLog.action == AuditAction.APPROVAL_GRANTED)).first()
    assert client.post(f"/approvals/{a.id}/approve", headers=_h(admin_token), json={}).status_code == 409


def test_ablehnen_braucht_begruendung(client, admin_token):
    _cleanup()
    a = _antrag()
    assert client.post(f"/approvals/{a.id}/reject", headers=_h(admin_token), json={"notes": "  "}).status_code == 422
    r = client.post(f"/approvals/{a.id}/reject", headers=_h(admin_token), json={"notes": "Quelle veraltet"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert r.json()["decision_notes"] == "Quelle veraltet"


def test_unbekannter_antrag(client, admin_token):
    assert client.post("/approvals/999999/approve", headers=_h(admin_token), json={}).status_code == 404
