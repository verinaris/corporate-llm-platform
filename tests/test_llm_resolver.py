"""
Tests für app/llm/resolver.py — die eine Wahrheit über Modell → Provider.

Der wichtigste Test ist test_models_endpoint_stimmt_mit_resolver_ueberein:
Er hält die Wahrheit an EINER Stelle. Driftet die hardcodierte is_local-
Angabe in app/api/models.py vom Resolver ab, wird er rot — statt dass eine
Datenresidenz-Policy still das Falsche tut.
"""

import pytest

from app.llm.resolver import (
    Provider,
    UnknownModelError,
    is_local_model,
    resolve_provider,
)


@pytest.mark.parametrize(
    "model,erwartet",
    [
        ("claude-sonnet-4-6", Provider.ANTHROPIC),
        ("claude-haiku-4-5", Provider.ANTHROPIC),
        ("claude-opus-4-7", Provider.ANTHROPIC),
        ("qwen2.5:7b", Provider.OLLAMA),
        ("llama3.1:8b", Provider.OLLAMA),
        ("mistral", Provider.OLLAMA),
        ("Qwen2.5:7B", Provider.OLLAMA),
    ],
)
def test_resolve_provider(model, erwartet):
    assert resolve_provider(model) is erwartet


@pytest.mark.parametrize("model", ["gpt-4", "gemini-pro", "", "irgendwas"])
def test_unbekanntes_modell_wirft(model):
    with pytest.raises(UnknownModelError):
        resolve_provider(model)


def test_is_local_model():
    assert is_local_model("qwen2.5:7b") is True
    assert is_local_model("claude-sonnet-4-6") is False


def test_models_endpoint_stimmt_mit_resolver_ueberein():
    """
    Die Anthropic-Liste in app/api/models.py deklariert is_local von Hand.
    Der Resolver leitet es her. Beide müssen dasselbe sagen.
    """
    from app.api.models import _ANTHROPIC_MODELS

    for m in _ANTHROPIC_MODELS:
        assert is_local_model(m.id) == m.is_local, (
            f"{m.id}: models.py sagt is_local={m.is_local}, "
            f"resolver sagt {is_local_model(m.id)}"
        )
