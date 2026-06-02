"""Tests für die Phase-4-Erweiterung (Ollama + Pricing)."""

import pytest

from app.pricing import calculate_cost, get_pricing, is_local_model


# ============================================================ #
# Pricing — Cloud-Modelle bleiben unverändert
# ============================================================ #

def test_pricing_claude_sonnet():
    assert get_pricing("claude-sonnet-4-6") == (3.00, 15.00)


def test_pricing_claude_opus():
    assert get_pricing("claude-opus-4-7") == (15.00, 75.00)


def test_pricing_unknown_model_default():
    """Unbekannte Modelle: Default-Preis (sicherheitshalber Sonnet)."""
    assert get_pricing("claude-totally-new-model") == (3.00, 15.00)


# ============================================================ #
# Pricing — Lokale Modelle = 0
# ============================================================ #

def test_pricing_qwen_known():
    assert get_pricing("qwen2.5:7b") == (0.0, 0.0)


def test_pricing_llama_known():
    assert get_pricing("llama3.1:8b") == (0.0, 0.0)


def test_pricing_unknown_local_via_prefix():
    """Modell mit lokalem Prefix → 0$ auch wenn nicht explizit gelistet."""
    assert get_pricing("llama3.5:42b") == (0.0, 0.0)
    assert get_pricing("qwen2.5:99b") == (0.0, 0.0)


def test_pricing_unknown_version_falls_back_to_stem():
    """qwen2.5:latest sollte als qwen-Modell erkannt werden."""
    p_in, p_out = get_pricing("qwen2.5:latest")
    assert p_in == 0.0
    assert p_out == 0.0


# ============================================================ #
# is_local_model
# ============================================================ #

@pytest.mark.parametrize("model_id", [
    "llama3.2:3b",
    "qwen2.5:7b",
    "mistral:7b",
    "phi3:3.8b",
    "gemma2:9b",
    "codellama:13b",
    "Llama-something",   # case-insensitive
    "QWEN2.5:14B",
])
def test_is_local_model_true(model_id):
    assert is_local_model(model_id)


@pytest.mark.parametrize("model_id", [
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "gpt-4-turbo",
    "completely-unknown",
])
def test_is_local_model_false(model_id):
    assert not is_local_model(model_id)


# ============================================================ #
# calculate_cost
# ============================================================ #

def test_calculate_cost_anthropic():
    """1000 Input + 1000 Output bei Sonnet = $0.018"""
    cost = calculate_cost("claude-sonnet-4-6", 1000, 1000)
    assert cost == round((3.00 + 15.00) / 1000, 6)


def test_calculate_cost_ollama_is_zero():
    """Lokale Modelle: immer 0 — egal wie viele Tokens."""
    cost = calculate_cost("qwen2.5:7b", 100_000, 100_000)
    assert cost == 0.0


def test_calculate_cost_zero_tokens():
    cost = calculate_cost("claude-sonnet-4-6", 0, 0)
    assert cost == 0.0
