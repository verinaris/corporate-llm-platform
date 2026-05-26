"""Tests für /users-Endpoints (nur Admin)."""


def test_list_users_requires_admin(client, user_token):
    """Nicht-Admins dürfen User-Liste NICHT sehen."""
    r = client.get(
        "/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 403


def test_list_users_as_admin(client, admin_token):
    r = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_user_as_admin(client, admin_token):
    r = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "neuer@example.com",
            "password": "GeheimGeheim1!",
            "role": "pharma-referent",
            "branch": "pharma",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "neuer@example.com"
    assert body["role"] == "pharma-referent"
    assert body["branch"] == "pharma"


def test_create_user_duplicate_email(client, admin_token, regular_user):
    r = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "user@example.com",  # existiert schon
            "password": "GeheimGeheim1!",
        },
    )
    assert r.status_code == 409


def test_create_user_password_too_short(client, admin_token):
    r = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "kurz@example.com",
            "password": "kurz",  # zu kurz
        },
    )
    assert r.status_code == 422
