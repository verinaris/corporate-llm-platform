"""Tests für Auth-Endpoints."""


def test_login_success(client, regular_user):
    r = client.post(
        "/auth/login",
        data={"username": "user@test.local", "password": "UserPass123!"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@test.local"
    assert body["user"]["role"] == "user"


def test_login_wrong_password(client, regular_user):
    r = client.post(
        "/auth/login",
        data={"username": "user@test.local", "password": "WRONG"},
    )
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post(
        "/auth/login",
        data={"username": "ghost@test.local", "password": "any"},
    )
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(client, user_token):
    r = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.local"


def test_invalid_token_rejected(client):
    r = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401
