"""Tests: Passwort zuruecksetzen + Selbstschutz des Admins."""


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _me(client, token):
    return client.get("/auth/me", headers=_h(token)).json()


def test_reset_password_flow(client, admin_token, user_token):
    target = _me(client, user_token)
    r = client.post(f"/users/{target['id']}/reset-password", headers=_h(admin_token))
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    pw = r.json()["temporary_password"]
    assert len(pw) == 16
    assert r.json()["user"]["must_change_password"] is True

    login = client.post("/auth/login", data={"username": target["email"], "password": pw})
    assert login.status_code == 200
    assert login.json()["user"]["must_change_password"] is True


def test_nicht_admin_darf_nicht_zuruecksetzen(client, admin_token, user_token):
    admin = _me(client, admin_token)
    r = client.post(f"/users/{admin['id']}/reset-password", headers=_h(user_token))
    assert r.status_code == 403


def test_admin_sperrt_sich_nicht_selbst_aus(client, admin_token):
    me = _me(client, admin_token)
    assert client.post(f"/users/{me['id']}/reset-password", headers=_h(admin_token)).status_code == 400
    assert client.delete(f"/users/{me['id']}", headers=_h(admin_token)).status_code == 400
    assert client.patch(f"/users/{me['id']}", headers=_h(admin_token),
                        json={"is_active": False}).status_code == 400
    assert client.patch(f"/users/{me['id']}", headers=_h(admin_token),
                        json={"role": "user"}).status_code == 400
