"""
Tests fuer AutomationTool — der Basistyp fuer freigabepflichtige Automationen.

Der wichtigste Test ist test_freigabepflicht_nicht_abschaltbar: Er sichert das
Kernversprechen ab, dass eine generierende Automation ohne Human-in-the-Loop
nicht baubar ist.
"""

import pytest

from app.tools.automation_base import AutomationTool
from app.tools.base import BaseTool


class _DummyAutomation(AutomationTool):
    """Minimale Automation zum Testen."""

    name = "dummy_automation"
    description = "Test"
    parameters_schema = {"type": "object", "properties": {}}
    allowed_roles = ["qualified-reviewer", "admin"]

    def generate(self, params, user_id=None):
        return {"draft": "Entwurfstext", "meta": {}}

    def execute(self, params, user_id=None):
        return {"published": True}


def test_ist_ein_basetool():
    assert issubclass(AutomationTool, BaseTool)


def test_dummy_laesst_sich_instanziieren():
    assert _DummyAutomation().name == "dummy_automation"


def test_freigabepflicht_ist_an():
    assert _DummyAutomation().requires_human_oversight is True


def test_freigabepflicht_nicht_abschaltbar():
    """
    Das Kernversprechen: eine Automation kann die Freigabepflicht nicht
    ausschalten. requires_human_oversight ist eine property ohne Setter --
    der Versuch, sie zu ueberschreiben, muss scheitern.
    """
    t = _DummyAutomation()
    with pytest.raises(AttributeError):
        t.requires_human_oversight = False


def test_generate_und_execute_sind_pflicht():
    """Ohne beide Methoden ist die Automation abstrakt und nicht instanziierbar."""

    class _Unvollstaendig(AutomationTool):
        name = "kaputt"

        def generate(self, params, user_id=None):
            return {"draft": ""}
        # execute fehlt absichtlich

    with pytest.raises(TypeError):
        _Unvollstaendig()
