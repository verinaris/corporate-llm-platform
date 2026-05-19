"""Tests für die Branchen-Plugin-Mechanik."""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy-for-tests")

from app.branches import get_plugin, list_branches  # noqa: E402
from app.branches.generic.plugin import GenericPlugin  # noqa: E402
from app.branches.pharma.plugin import PharmaPlugin  # noqa: E402
from app.schemas import ChatMessage  # noqa: E402


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


def test_generic_plugin_is_passthrough():
    """Generic darf nichts verändern."""
    plugin = GenericPlugin()
    msgs = [ChatMessage(role="user", content="Hallo")]

    assert plugin.get_system_prompt() is None
    assert plugin.pre_process_messages(msgs) == msgs
    assert plugin.post_process_response("Antwort") == "Antwort"
    assert plugin.required_disclaimer is None


def test_pharma_plugin_skeleton_is_currently_passthrough():
    """Pharma ist noch leeres Gerüst — Verhalten = Generic."""
    plugin = PharmaPlugin()
    msgs = [ChatMessage(role="user", content="Hallo")]

    assert plugin.get_system_prompt() is None
    assert plugin.pre_process_messages(msgs) == msgs
    assert plugin.post_process_response("Antwort") == "Antwort"
    assert plugin.required_disclaimer is None
