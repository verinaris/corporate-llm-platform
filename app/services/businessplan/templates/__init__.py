"""
Template-Registry — zentrale Stelle, an der alle Vorlagen registriert sind.

Erweitern: Neues Template-Modul anlegen (z.B. `pharma.py`), das eine
`INFO`-Konstante und `get_default_input()`-Funktion exportiert. Hier
in `_TEMPLATES` eintragen.
"""

from typing import Callable

from app.services.businessplan.models import BusinessPlanInput, TemplateInfo
from app.services.businessplan.templates import (
    kmu_default,
    pharma_beratung_vertrieb,
    verinaris,
)


# Registry: template_id → (Info, Default-Factory)
_TEMPLATES: dict[str, tuple[TemplateInfo, Callable[[], BusinessPlanInput]]] = {
    kmu_default.INFO.id: (kmu_default.INFO, kmu_default.get_default_input),
    pharma_beratung_vertrieb.INFO.id: (
        pharma_beratung_vertrieb.INFO,
        pharma_beratung_vertrieb.get_default_input,
    ),
    verinaris.INFO.id: (verinaris.INFO, verinaris.get_default_input),
}


def list_templates() -> list[TemplateInfo]:
    """Liefert alle verfügbaren Templates (für Dropdown)."""
    return [info for info, _ in _TEMPLATES.values()]


def get_template_default(template_id: str) -> BusinessPlanInput:
    """
    Liefert die Default-Werte zu einer Template-ID.

    Fallback auf KMU-Default wenn unbekannt.
    """
    if template_id in _TEMPLATES:
        _, factory = _TEMPLATES[template_id]
        return factory()
    return kmu_default.get_default_input()


def get_template_info(template_id: str) -> TemplateInfo | None:
    """Liefert die Info zu einer Template-ID oder None."""
    pair = _TEMPLATES.get(template_id)
    return pair[0] if pair else None
