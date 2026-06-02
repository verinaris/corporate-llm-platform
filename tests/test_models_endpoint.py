"""Tests für /models/available Endpoint (Phase 4)."""

import pytest


def test_available_models_requires_login(client):
    r = client.get("/models/available")
    assert r.status_code == 401


def test_available_models_response_shape(client, user_token, monkeypatch):
    """Sicherstellen dass Endpoint funktioniert, auch wenn Ollama down ist."""
    # Ollama-Aufruf mocken, dass kein Ollama-Server vorhanden ist
    async def fake_list():
        return []

    from app.api import models as models_module
    monkeypatch.setattr(models_module, "list_installed_models", fake_list)

    r = client.get(
        "/models/available",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "providers" in body
    assert "default_model" in body

    provider_names = [p["name"] for p in body["providers"]]
    assert "anthropic" in provider_names
    assert "ollama" in provider_names


def test_available_models_with_ollama_models(client, user_token, monkeypatch):
    """Wenn Ollama Modelle hat, tauchen sie in der Liste auf."""
    async def fake_list():
        return [
            {"name": "qwen2.5:7b", "size_bytes": 4_700_000_000, "modified_at": ""},
            {"name": "llama3.2:3b", "size_bytes": 2_000_000_000, "modified_at": ""},
        ]

    from app.api import models as models_module
    monkeypatch.setattr(models_module, "list_installed_models", fake_list)

    r = client.get(
        "/models/available",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    ollama = next(p for p in body["providers"] if p["name"] == "ollama")
    assert ollama["available"] is True
    ollama_ids = [m["id"] for m in ollama["models"]]
    assert "qwen2.5:7b" in ollama_ids
    assert "llama3.2:3b" in ollama_ids

    # Lokale Modelle sind als is_local markiert
    for m in ollama["models"]:
        assert m["is_local"] is True
        assert m["provider"] == "ollama"


def test_available_models_when_ollama_offline(client, user_token, monkeypatch):
    """Ollama-Provider wird trotzdem gelistet, aber mit available=False."""
    async def fake_list():
        return []

    from app.api import models as models_module
    monkeypatch.setattr(models_module, "list_installed_models", fake_list)

    r = client.get(
        "/models/available",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200
    ollama = next(p for p in r.json()["providers"] if p["name"] == "ollama")
    assert ollama["available"] is False
    assert ollama["note"] is not None
    assert "ollama serve" in ollama["note"]
