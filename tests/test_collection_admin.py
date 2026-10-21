"""Ende-zu-Ende-Tests fuer die Rechtevergabe an Sammlungen (E4)."""


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _email(client, token):
    return client.get("/auth/me", headers=_h(token)).json()["email"]


def _sichtbar(client, token):
    return [c["name"] for c in client.get("/documents/collections", headers=_h(token)).json()]


def test_nicht_admin_wird_abgewiesen(client, user_token):
    assert client.get("/admin/collections", headers=_h(user_token)).status_code == 403


def test_vergeben_entziehen_sichtbarkeit_besitz(client, admin_token, user_token):
    admin_mail = _email(client, admin_token)
    user_mail = _email(client, user_token)
    assert client.post("/documents/collections", headers=_h(admin_token),
                       data={"name": "akte-e4"}).status_code == 201

    # Uebersicht zeigt Besitzer
    alle = {c["name"]: c for c in client.get("/admin/collections", headers=_h(admin_token)).json()}
    assert alle["akte-e4"]["owner"] == admin_mail
    assert "akte-e4" not in _sichtbar(client, user_token)

    # Vergeben -> User sieht sie
    r = client.post("/admin/collections/akte-e4/members", headers=_h(admin_token),
                    json={"email": user_mail, "level": "read"})
    assert r.status_code == 200
    assert "akte-e4" in _sichtbar(client, user_token)

    # Entziehen -> weg
    assert client.delete(f"/admin/collections/akte-e4/members/{user_mail}",
                         headers=_h(admin_token)).status_code == 200
    assert "akte-e4" not in _sichtbar(client, user_token)

    # Fuer alle lesbar -> User sieht sie wieder
    assert client.put("/admin/collections/akte-e4/visibility", headers=_h(admin_token),
                      json={"open_for_all": True}).status_code == 200
    assert "akte-e4" in _sichtbar(client, user_token)
    client.put("/admin/collections/akte-e4/visibility", headers=_h(admin_token),
               json={"open_for_all": False})

    # Besitz uebertragen -> User ist Besitzer, Admin sieht sie nicht mehr
    r = client.put("/admin/collections/akte-e4/owner", headers=_h(admin_token),
                   json={"email": user_mail})
    assert r.status_code == 200 and r.json()["owner"] == user_mail
    assert "akte-e4" in _sichtbar(client, user_token)
    assert "akte-e4" not in _sichtbar(client, admin_token)


def test_besitzer_kann_nicht_mitglied_werden(client, admin_token):
    admin_mail = _email(client, admin_token)
    client.post("/documents/collections", headers=_h(admin_token), data={"name": "akte-e4b"})
    r = client.post("/admin/collections/akte-e4b/members", headers=_h(admin_token),
                    json={"email": admin_mail, "level": "read"})
    assert r.status_code == 400


def test_unbekannte_sammlung_und_user(client, admin_token):
    assert client.post("/admin/collections/gibt-es-nicht/members", headers=_h(admin_token),
                       json={"email": "x@y.de"}).status_code == 404
    client.post("/documents/collections", headers=_h(admin_token), data={"name": "akte-e4c"})
    assert client.post("/admin/collections/akte-e4c/members", headers=_h(admin_token),
                       json={"email": "niemand@nirgends.de"}).status_code == 404
