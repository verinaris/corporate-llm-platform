"""Smoke-Tests."""

import os

# Test braucht einen Dummy-Key, damit Settings nicht crashen
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy-for-tests")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_stats_initially_empty():
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_requests"] >= 0
    assert isinstance(body["by_model"], dict)
