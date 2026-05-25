"""Smoke-Tests für Health-/Stats-Endpoints."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_stats_requires_login(client):
    """Stats ohne Token soll 401 zurückgeben."""
    r = client.get("/stats")
    assert r.status_code == 401


def test_stats_with_user_token(client, user_token):
    """Mit Token soll es funktionieren."""
    r = client.get(
        "/stats",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_requests"] >= 0
