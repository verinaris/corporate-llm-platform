"""Tests: Ausfuehrung nach der Freigabe (F2)."""

import json

import pytest
from sqlmodel import Session, select

from app.database import engine
from app.models import PendingApproval, User
from app.tools.base import BaseTool
from app.tools.registry import ApprovalPendingError, PermissionDeniedError, ToolRegistry


class _SyncTool(BaseTool):
    name = "test_sync_oversight"
    requires_human_oversight = True
    allowed_roles = ["user", "admin"]

    def execute(self, params, user_id=None):
        return {"ok": True, "echo": params, "user_id": user_id}


class _AsyncTool(BaseTool):
    name = "test_async_oversight"
    requires_human_oversight = True
    allowed_roles = ["user", "admin"]

    async def execute(self, params, user_id=None):
        return {"ok": True, "async": True, "user_id": user_id}


class _FailTool(BaseTool):
    name = "test_fail_oversight"
    requires_human_oversight = True
    allowed_roles = ["user", "admin"]

    def execute(self, params, user_id=None):
        return {"ok": False, "error": "Quelle nicht erreichbar"}


@pytest.fixture(autouse=True)
def _tools():
    tools = [_SyncTool(), _AsyncTool(), _FailTool()]
    for t in tools:
        ToolRegistry._tools[t.name] = t
    yield
    for t in tools:
        ToolRegistry._tools.pop(t.name, None)
    with Session(engine) as s:
        for r in s.exec(select(PendingApproval)).all():
            s.delete(r)
        s.commit()


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _beantragen(tool, params, regular_user):
    with pytest.raises(ApprovalPendingError) as exc:
        ToolRegistry.execute(tool, params, user_id=regular_user.id, user_role="user", user_email=regular_user.email)
    return exc.value.request_id


def test_freigabe_fuehrt_mit_konto_des_antragstellers_aus(client, admin_token, regular_user):
    rid = _beantragen("test_sync_oversight", {"x": 1}, regular_user)
    r = client.post(f"/approvals/{rid}/approve", headers=_h(admin_token), json={})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved" and body["execution_status"] == "succeeded"
    result = json.loads(body["execution_result"])
    assert result["echo"] == {"x": 1}
    assert result["user_id"] == regular_user.id   # nicht der Admin


def test_async_tool_wird_wirklich_ausgefuehrt(client, admin_token, regular_user):
    rid = _beantragen("test_async_oversight", {"y": 2}, regular_user)
    body = client.post(f"/approvals/{rid}/approve", headers=_h(admin_token), json={}).json()
    assert body["execution_status"] == "succeeded"
    assert json.loads(body["execution_result"])["async"] is True


def test_fehlschlag_wird_festgehalten(client, admin_token, regular_user):
    rid = _beantragen("test_fail_oversight", {}, regular_user)
    body = client.post(f"/approvals/{rid}/approve", headers=_h(admin_token), json={}).json()
    assert body["execution_status"] == "failed"
    assert "nicht erreichbar" in body["execution_result"]


def test_token_nur_einmal_nutzbar(client, admin_token, regular_user):
    rid = _beantragen("test_sync_oversight", {"z": 3}, regular_user)
    client.post(f"/approvals/{rid}/approve", headers=_h(admin_token), json={})
    with Session(engine) as s:
        token = s.get(PendingApproval, rid).approval_token
    with pytest.raises(PermissionDeniedError):
        ToolRegistry.execute("test_sync_oversight", {"z": 3}, user_role="user",
                             user_email=regular_user.email, approval_token=token)


def test_inaktiver_antragsteller_wird_nicht_ausgefuehrt(client, admin_token, regular_user):
    rid = _beantragen("test_sync_oversight", {"w": 4}, regular_user)
    with Session(engine) as s:
        u = s.get(User, regular_user.id)
        u.is_active = False
        s.add(u)
        s.commit()
    body = client.post(f"/approvals/{rid}/approve", headers=_h(admin_token), json={}).json()
    assert body["execution_status"] == "skipped"


def test_sync_execute_lehnt_async_tool_ab(regular_user):
    rid = _beantragen("test_async_oversight", {"v": 5}, regular_user)
    from app.services.approval_request import approve_request
    _, token = approve_request(rid, "chef@example.com", "admin")
    with pytest.raises(TypeError):
        ToolRegistry.execute("test_async_oversight", {"v": 5}, user_role="user",
                             user_email=regular_user.email, approval_token=token)
