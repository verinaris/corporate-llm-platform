"""
Branchen-Plugin-Registry.

Hier werden alle Plugins registriert. Wenn du eine neue Branche
hinzufügst:

1. Lege einen neuen Ordner `app/branches/<branch_code>/` an
2. Implementiere dort `plugin.py` mit einer BranchPlugin-Subklasse
3. Füge die Klasse hier zum _REGISTRY hinzu

Zugriff überall via:
    from app.branches import get_plugin
    plugin = get_plugin("pharma")   # liefert PharmaPlugin-Instanz
"""

from app.branches.base import BranchPlugin
from app.branches.generic.plugin import GenericPlugin
from app.branches.pharma.plugin import PharmaPlugin

# Registry: branch_code → Plugin-Klasse
_REGISTRY: dict[str, type[BranchPlugin]] = {
    "generic": GenericPlugin,
    "pharma": PharmaPlugin,
    # "legal": LegalPlugin,     # später
    # "tax": TaxPlugin,         # später
    # "medical": MedicalPlugin, # später
    # "craft": CraftPlugin,     # später
}


def get_plugin(branch_code: str | None) -> BranchPlugin:
    """
    Liefert eine Plugin-Instanz für den Branchen-Code.

    Unbekannte oder leere Codes → GenericPlugin (kein Eingriff).
    """
    if not branch_code:
        return GenericPlugin()
    plugin_class = _REGISTRY.get(branch_code, GenericPlugin)
    return plugin_class()


def list_branches() -> list[str]:
    """Liefert die Liste aller registrierten Branchen-Codes."""
    return list(_REGISTRY.keys())


__all__ = ["BranchPlugin", "get_plugin", "list_branches"]
