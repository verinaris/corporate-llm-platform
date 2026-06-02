"""Tests für den Ollama-Client (Phase 4)."""

import pytest

from app.llm.ollama_client import OllamaClient
from app.schemas import ChatMessage


@pytest.fixture
def ollama_response_ok():
    """Realistische Ollama-API-Antwort."""
    return {
        "model": "qwen2.5:7b",
        "created_at": "2026-06-02T10:00:00Z",
        "message": {
            "role": "assistant",
            "content": "Hallo! Wie kann ich dir helfen?",
        },
        "done": True,
        "total_duration": 1234567890,
        "load_duration": 12345,
        "prompt_eval_count": 17,
        "prompt_eval_duration": 234567,
        "eval_count": 42,
        "eval_duration": 1234567,
    }


@pytest.mark.asyncio
async def test_ollama_chat_returns_llm_response(monkeypatch, ollama_response_ok):
    """Happy-Path: Ollama liefert Antwort → unser Client wandelt um."""
    import httpx

    class MockResponse:
        status_code = 200
        text = ""

        def json(self):
            return ollama_response_ok

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    client = OllamaClient()
    result = await client.chat(
        messages=[ChatMessage(role="user", content="Hallo")],
        model="qwen2.5:7b",
        max_tokens=100,
    )

    assert result.content == "Hallo! Wie kann ich dir helfen?"
    assert result.provider == "ollama"
    assert result.model == "qwen2.5:7b"
    assert result.input_tokens == 17
    assert result.output_tokens == 42


@pytest.mark.asyncio
async def test_ollama_chat_404_model_missing(monkeypatch):
    """Wenn das Modell nicht installiert ist: hilfreiche Fehlermeldung."""
    import httpx

    class MockResponse:
        status_code = 404
        text = '{"error":"model not found"}'

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    client = OllamaClient()
    with pytest.raises(RuntimeError) as exc_info:
        await client.chat(
            messages=[ChatMessage(role="user", content="Hi")],
            model="nicht-installiertes-modell:99b",
            max_tokens=100,
        )
    assert "ollama pull" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_chat_server_offline(monkeypatch):
    """Wenn Ollama-Server nicht läuft: klare Fehlermeldung."""
    import httpx

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None):
            raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    client = OllamaClient()
    with pytest.raises(RuntimeError) as exc_info:
        await client.chat(
            messages=[ChatMessage(role="user", content="Hi")],
            model="qwen2.5:7b",
            max_tokens=100,
        )
    assert "ollama serve" in str(exc_info.value).lower()


# ============================================================ #
# Resolver — sucht der Chat-Endpoint den richtigen Client?
# ============================================================ #

def test_resolver_picks_anthropic_for_claude():
    from app.api.chat import _resolve_client
    from app.llm.anthropic_client import AnthropicClient

    client = _resolve_client("claude-sonnet-4-6")
    assert isinstance(client, AnthropicClient)


def test_resolver_picks_ollama_for_known_local():
    from app.api.chat import _resolve_client
    from app.llm.ollama_client import OllamaClient

    for model in ("qwen2.5:7b", "llama3.1:8b", "mistral:7b"):
        client = _resolve_client(model)
        assert isinstance(client, OllamaClient), f"failed for {model}"


def test_resolver_rejects_unknown():
    from app.api.chat import _resolve_client
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        _resolve_client("gpt-4-turbo")
    assert exc_info.value.status_code == 400
