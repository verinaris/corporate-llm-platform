"""
Zentrales Branchen-Profile-Modul.

Das `User.branch`-Feld ist der **zentrale Schalter** der Plattform.
Hier wird definiert:

- Welche Branchen gibt es (UserBranch-Enum erweitern für neue)
- Wie sie heißen (für UI-Anzeige)
- Welche Module sie wie konfigurieren

**Designprinzip:**
- Module fragen NICHT direkt `User.branch == "pharma"`
- Module fragen IMMER über dieses Modul: `get_industry_for_businessplan(user.branch)`
→ So bleibt die Mapping-Logik an EINER Stelle.
"""

from dataclasses import dataclass

from app.models import UserBranch


@dataclass(frozen=True)
class IndustryProfile:
    """Anzeige-Metadaten für ein Branchen-Profil."""

    code: str           # = UserBranch-Wert (z.B. "pharma")
    name: str           # User-friendly: "Pharma-Beratung & Vertrieb"
    short_name: str     # Sidebar: "Pharma"
    icon: str           # Emoji für UI
    description: str    # 1-Zeilen-Beschreibung

    # --- Policy -------------------------------------------------- #
    # Bewusst OHNE Default: Wer eine Branche anlegt, MUSS diese Fragen
    # beantworten. "Vergessen" darf nicht "unreguliert" bedeuten.
    self_assignable: bool       # Darf ein User sich die Branche selbst geben?
    allow_cloud_models: bool    # Duerfen Daten das eigene Netz verlassen?
    default_model: str | None   # Vorgabe-Modell; None = settings.default_model

    is_default: bool = False


# ============================================================ #
# Profil-Definitionen
# ============================================================ #

_PROFILES: dict[str, IndustryProfile] = {
    "generic": IndustryProfile(
        code="generic",
        name="Generisch / Keine Spezialisierung",
        short_name="Generic",
        icon="🌐",
        description=(
            "Branchenneutrale Plattform-Nutzung. Keine Industry-spezifischen "
            "Filter, Vorlagen oder Checks. Geeignet für gemischte Use-Cases."
        ),
        is_default=True,
        self_assignable=True,
        allow_cloud_models=True,
        default_model=None,
    ),
    "pharma": IndustryProfile(
        code="pharma",
        name="Pharma-Beratung & Vertrieb",
        short_name="Pharma",
        icon="💊",
        description=(
            "Compliance-Filter für HWG/AMG/FSA-Kodex aktiv. "
            "Industry-Checks (Pharmakovigilanz, DSGVO Art. 9) im Businessplan. "
            "Cloud-Modelle gesperrt — Daten bleiben auf eigener Hardware."
        ),
        self_assignable=False,
        allow_cloud_models=False,
        default_model="qwen2.5:7b",
    ),
    # später: legal, tax, energy, craft, medical
}


# ============================================================ #
# Public API — Anzeige
# ============================================================ #

def list_industry_profiles() -> list[IndustryProfile]:
    """Liefert alle Branchen-Profile (sortiert: Generic zuerst, dann alphabet.)."""
    profiles = list(_PROFILES.values())
    profiles.sort(key=lambda p: (not p.is_default, p.name))
    return profiles


def get_industry_profile(code: str | UserBranch | None) -> IndustryProfile:
    """
    Liefert das Profil zu einem Code. Fallback auf Generic.
    """
    if code is None:
        return _PROFILES["generic"]
    if isinstance(code, UserBranch):
        code = code.value
    return _PROFILES.get(code, _PROFILES["generic"])


# ============================================================ #
# Module-Mappings (von zentral nach modul-spezifisch)
# ============================================================ #

# Mapping: User.branch → BusinessPlanInput.industry
_BRANCH_TO_BP_INDUSTRY: dict[str, str] = {
    "generic": "generic",
    "pharma": "pharma_beratung_vertrieb",
}


def get_industry_for_businessplan(branch: str | UserBranch | None) -> str:
    """
    Mapping: User-Branche → Businessplan-Industry-Code.

    Nutzung in `app/api/businessplan.py`:
        bp_industry = get_industry_for_businessplan(current_user.branch)
    """
    if branch is None:
        return "generic"
    if isinstance(branch, UserBranch):
        branch = branch.value
    return _BRANCH_TO_BP_INDUSTRY.get(branch, "generic")


# Mapping: User.branch → Set von Businessplan-Template-IDs (Filter)
_BRANCH_TO_BP_TEMPLATES: dict[str, set[str]] = {
    "generic": {"kmu_default", "verinaris_beispiel"},
    "pharma": {"pharma_beratung_vertrieb", "kmu_default", "verinaris_beispiel"},
    # Generic-User sehen: KMU-Standard + Verinaris-Beispiel
    # Pharma-User sehen: Pharma + KMU-Standard (als Fallback) + Verinaris-Beispiel
}


def get_businessplan_templates_for_branch(
    branch: str | UserBranch | None,
) -> set[str]:
    """
    Liefert die erlaubten Businessplan-Template-IDs für eine Branche.

    Nutzung: Filter im Vorlagen-Dropdown des Businessplan-Editors.
    Admin sieht alle Vorlagen (Override in API-Layer).
    """
    if branch is None:
        return _BRANCH_TO_BP_TEMPLATES["generic"]
    if isinstance(branch, UserBranch):
        branch = branch.value
    return _BRANCH_TO_BP_TEMPLATES.get(branch, _BRANCH_TO_BP_TEMPLATES["generic"])


# ============================================================ #
# Public API — Policy
# ============================================================ #

def branch_allows_cloud(branch: "str | UserBranch | None") -> bool:
    """
    Duerfen fuer diese Branche Cloud-Modelle genutzt werden?

    Nutzung in `app/api/chat.py` und `app/api/models.py`. Endpoints
    fragen NIE `branch == "pharma"` — immer ueber diese Funktion.
    """
    return get_industry_profile(branch).allow_cloud_models


def branch_default_model(branch: "str | UserBranch | None") -> str | None:
    """Vorgabe-Modell der Branche. None = globaler Default aus settings."""
    return get_industry_profile(branch).default_model


def branch_is_self_assignable(branch: "str | UserBranch | None") -> bool:
    """Darf ein User sich diese Branche selbst geben — ohne Admin?"""
    return get_industry_profile(branch).self_assignable


__all__ = [
    "IndustryProfile",
    "list_industry_profiles",
    "get_industry_profile",
    "get_industry_for_businessplan",
    "get_businessplan_templates_for_branch",
    "branch_allows_cloud",
    "branch_default_model",
    "branch_is_self_assignable",
]
