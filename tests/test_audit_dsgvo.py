"""Tests für Audit-Log + DSGVO-Funktionen (Phase 6a)."""

import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine
from app.models import AuditAction, AuditLog, User
from app.services import audit


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# Audit-Service: Basis-Funktionalität ---------------------------------------

def test_audit_log_writes_entry():
    with Session(engine) as session:
        before = len(session.exec(select(AuditLog)).all())

    audit.log(
        user_email="audit-test@example.com",
        action=AuditAction.LOGIN,
        user_role="user",
        ip_address="127.0.0.1",
    )

    with Session(engine) as session:
        after = len(session.exec(select(AuditLog)).all())
    assert after == before + 1


def test_audit_log_details_serialized_as_json():
    audit.log(
        user_email="json-test@example.com",
        action=AuditAction.BRANCH_CHANGED,
        details={"from": "generic", "to": "pharma"},
    )
    with Session(engine) as session:
        entry = session.exec(
            select(AuditLog).where(AuditLog.user_email == "json-test@example.com")
        ).first()
        assert entry is not None
        data = json.loads(entry.details)
        assert data["from"] == "generic"


def test_audit_log_does_not_raise_on_db_error(monkeypatch):
    from app.services import audit as audit_module
    def broken(*a, **k): raise RuntimeError("DB down")
    monkeypatch.setattr(audit_module, "Session", broken)
    audit.log(user_email="x@x.com", action=AuditAction.LOGIN)  # darf NICHT werfen


# Login-Audit-Hook ---------------------------------------------------------

def test_login_failed_creates_audit_entry(client: TestClient):
    client.post("/auth/login", data={"username": "ghost@example.com", "password": "wrong"})
    with Session(engine) as session:
        entry = session.exec(
            select(AuditLog)
            .where(AuditLog.user_email == "ghost@example.com")
            .where(AuditLog.action == AuditAction.LOGIN_FAILED)
        ).first()
        assert entry is not None
        assert entry.success is False


def test_successful_login_creates_audit_entry(client: TestClient, regular_user):
    r = client.post("/auth/login", data={
        "username": "user@example.com", "password": "UserPass123!",
    })
    assert r.status_code == 200
    with Session(engine) as session:
        entry = session.exec(
            select(AuditLog)
            .where(AuditLog.user_email == "user@example.com")
            .where(AuditLog.action == AuditAction.LOGIN)
        ).first()
        assert entry is not None
        assert entry.success is True


# Admin-API: Zugriffsschutz ------------------------------------------------

def test_audit_log_requires_admin_or_compliance(client: TestClient, user_token: str):
    r = client.get("/admin/audit-log", headers=_auth_headers(user_token))
    assert r.status_code == 403


def test_dsgvo_delete_requires_admin(client: TestClient, user_token: str):
    r = client.delete("/admin/users/1/dsgvo-delete", headers=_auth_headers(user_token))
    assert r.status_code == 403


def test_dsgvo_export_requires_admin(client: TestClient, user_token: str):
    r = client.get("/admin/users/1/dsgvo-export", headers=_auth_headers(user_token))
    assert r.status_code == 403


# Admin-API: Lesen + Filter ------------------------------------------------

def test_admin_can_read_audit_log(client: TestClient, admin_token: str):
    r = client.get("/admin/audit-log?limit=10", headers=_auth_headers(admin_token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_log_filter_by_action(client: TestClient, admin_token: str):
    audit.log(
        user_email="filter-test@example.com",
        action=AuditAction.PLAN_CREATED,
        target_type="business_plan", target_id="42",
    )
    r = client.get(
        "/admin/audit-log?action=plan_created&limit=50",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 200
    assert all(e["action"] == "plan_created" for e in r.json())


def test_audit_log_invalid_action_returns_400(client: TestClient, admin_token: str):
    r = client.get(
        "/admin/audit-log?action=invalid_xyz",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 400


def test_audit_actions_list(client: TestClient, admin_token: str):
    r = client.get("/admin/audit-log/actions", headers=_auth_headers(admin_token))
    assert r.status_code == 200
    actions = r.json()
    assert "login" in actions
    assert "user_full_delete" in actions


# DSGVO Art. 17 ------------------------------------------------------------

def test_admin_cannot_delete_themselves(client: TestClient, admin_token: str, admin_user):
    r = client.delete(
        f"/admin/users/{admin_user.id}/dsgvo-delete",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 400
    assert "selbst" in r.json()["detail"].lower()


def test_dsgvo_delete_unknown_user_returns_404(client: TestClient, admin_token: str):
    r = client.delete(
        "/admin/users/99999/dsgvo-delete",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 404


def test_dsgvo_full_delete_pseudonymizes_audit(
    client: TestClient, admin_token: str, regular_user,
):
    audit.log(user_email=regular_user.email, action=AuditAction.LOGIN)

    r = client.delete(
        f"/admin/users/{regular_user.id}/dsgvo-delete",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 200
    report = r.json()
    pseudonym = report["user_email_pseudonym"]
    assert pseudonym.startswith("deleted_user_")

    with Session(engine) as session:
        old = session.exec(
            select(AuditLog).where(AuditLog.user_email == "user@example.com")
        ).all()
        new = session.exec(
            select(AuditLog).where(AuditLog.user_email == pseudonym)
        ).all()
        assert len(old) == 0
        assert len(new) >= 1

    with Session(engine) as session:
        deleted = session.get(User, regular_user.id)
        assert deleted is not None
        assert deleted.email == pseudonym
        assert deleted.is_active is False


def test_dsgvo_export_returns_user_data(
    client: TestClient, admin_token: str, regular_user,
):
    r = client.get(
        f"/admin/users/{regular_user.id}/dsgvo-export",
        headers=_auth_headers(admin_token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == regular_user.email
    assert "documents" in data
    assert "business_plans" in data
    assert "audit_entries_count" in data
