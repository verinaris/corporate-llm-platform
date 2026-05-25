"""Tests für die Branchen-Plugin-Mechanik."""

from app.branches import get_plugin, list_branches
from app.branches.generic.plugin import GenericPlugin
from app.branches.pharma.plugin import PharmaPlugin
from app.branches.pharma.prompts import PHARMA_DISCLAIMER, PHARMA_SYSTEM_PROMPT
from app.schemas import ChatMessage


# ============================================================ #
# Registry
# ============================================================ #

def test_registry_lists_known_branches():
    branches = list_branches()
    assert "generic" in branches
    assert "pharma" in branches


def test_get_plugin_generic():
    plugin = get_plugin("generic")
    assert isinstance(plugin, GenericPlugin)
    assert plugin.branch_code == "generic"


def test_get_plugin_pharma():
    plugin = get_plugin("pharma")
    assert isinstance(plugin, PharmaPlugin)
    assert plugin.branch_code == "pharma"
    assert plugin.display_name == "Pharma-Außendienst"


def test_unknown_branch_falls_back_to_generic():
    plugin = get_plugin("does-not-exist")
    assert isinstance(plugin, GenericPlugin)


def test_none_branch_falls_back_to_generic():
    plugin = get_plugin(None)
    assert isinstance(plugin, GenericPlugin)


# ============================================================ #
# Generic-Plugin — Passthrough
# ============================================================ #

def test_generic_plugin_is_passthrough():
    plugin = GenericPlugin()
    msgs = [ChatMessage(role="user", content="Hallo")]

    assert plugin.get_system_prompt() is None
    assert plugin.pre_process_messages(msgs) == msgs
    assert plugin.post_process_response("Antwort") == "Antwort"
    assert plugin.required_disclaimer is None


# ============================================================ #
# Pharma-Plugin — Phase 2c
# ============================================================ #

def test_pharma_has_system_prompt():
    plugin = PharmaPlugin()
    prompt = plugin.get_system_prompt()
    assert prompt is not None
    assert "HWG" in prompt
    assert "Pharma" in prompt or "pharma" in prompt.lower()


def test_pharma_system_prompt_mentions_critical_topics():
    """Stellt sicher, dass der Prompt die wichtigen Compliance-Themen abdeckt."""
    plugin = PharmaPlugin()
    prompt = plugin.get_system_prompt() or ""
    # Kritische Begriffe, die im Prompt vorkommen MÜSSEN
    for term in ["HWG", "AMG", "BfArM", "DSGVO", "Quellen"]:
        assert term in prompt, f"Begriff '{term}' fehlt im Pharma-Prompt"


def test_pharma_disclaimer_is_appended():
    plugin = PharmaPlugin()
    answer = "Acetylsalicylsäure ist ein NSAR."
    processed = plugin.post_process_response(answer)
    assert answer in processed
    assert "Compliance-Hinweis" in processed
    assert "BfArM" in processed


def test_pharma_disclaimer_not_doubled():
    """Wenn der Disclaimer schon drin ist, wird er nicht nochmal angehängt."""
    plugin = PharmaPlugin()
    answer_with_disclaimer = "Eine Antwort." + PHARMA_DISCLAIMER
    processed = plugin.post_process_response(answer_with_disclaimer)
    # Disclaimer-Text darf nur einmal vorkommen
    assert processed.count("Compliance-Hinweis") == 1


def test_pharma_required_disclaimer():
    plugin = PharmaPlugin()
    assert plugin.required_disclaimer == PHARMA_DISCLAIMER


def test_pharma_pre_process_passthrough_for_now():
    """In Phase 2c noch Passthrough — PII-Filter kommt in Phase 3."""
    plugin = PharmaPlugin()
    msgs = [ChatMessage(role="user", content="Was sind Wechselwirkungen?")]
    assert plugin.pre_process_messages(msgs) == msgs
