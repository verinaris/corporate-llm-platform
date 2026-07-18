"""Tests für das zentrale Branchen-Profil-System."""

import pytest

from app.branches.profiles import (
    branch_allows_cloud,
    branch_default_model,
    branch_is_self_assignable,
    get_businessplan_templates_for_branch,
    get_industry_for_businessplan,
    get_industry_profile,
    list_industry_profiles,
)
from app.models import UserBranch


# ============================================================ #
# Profile-Listing
# ============================================================ #

def test_profiles_include_generic_and_pharma():
    profiles = list_industry_profiles()
    codes = [p.code for p in profiles]
    assert "generic" in codes
    assert "pharma" in codes


def test_generic_is_first():
    """Generic sollte als Default zuerst kommen."""
    profiles = list_industry_profiles()
    assert profiles[0].code == "generic"
    assert profiles[0].is_default is True


def test_pharma_profile_has_correct_metadata():
    profile = get_industry_profile("pharma")
    assert profile.code == "pharma"
    assert "Pharma" in profile.name
    assert profile.icon == "💊"
    assert profile.is_default is False


def test_unknown_branch_falls_back_to_generic():
    profile = get_industry_profile("does-not-exist")
    assert profile.code == "generic"


def test_none_branch_returns_generic():
    profile = get_industry_profile(None)
    assert profile.code == "generic"


def test_userbranch_enum_works():
    """Auch UserBranch-Enum als Eingabe akzeptiert."""
    profile = get_industry_profile(UserBranch.PHARMA)
    assert profile.code == "pharma"


# ============================================================ #
# Module-Mappings
# ============================================================ #

def test_pharma_maps_to_pharma_beratung_vertrieb():
    """User.branch=pharma → Businessplan-industry=pharma_beratung_vertrieb."""
    industry = get_industry_for_businessplan("pharma")
    assert industry == "pharma_beratung_vertrieb"


def test_generic_maps_to_generic_industry():
    industry = get_industry_for_businessplan("generic")
    assert industry == "generic"


def test_unknown_branch_falls_back_for_bp_industry():
    industry = get_industry_for_businessplan("xyz")
    assert industry == "generic"


def test_pharma_user_sees_pharma_template():
    """Pharma-User darf Pharma-Vorlage sehen."""
    allowed = get_businessplan_templates_for_branch("pharma")
    assert "pharma_beratung_vertrieb" in allowed


def test_generic_user_does_not_see_pharma_template():
    """Generic-User soll Pharma-Vorlage NICHT sehen (nur Admin sieht alles)."""
    allowed = get_businessplan_templates_for_branch("generic")
    assert "pharma_beratung_vertrieb" not in allowed
    assert "kmu_default" in allowed


def test_pharma_user_still_sees_kmu_default():
    """Pharma-User soll auch KMU-Standard als Fallback haben."""
    allowed = get_businessplan_templates_for_branch("pharma")
    assert "kmu_default" in allowed


# ============================================================ #
# Konsistenz mit Businessplan-Templates
# ============================================================ #

def test_all_branch_template_refs_actually_exist():
    """
    Sanity: Alle Template-IDs in _BRANCH_TO_BP_TEMPLATES müssen
    real existieren — sonst zeigt das UI tote Einträge.
    """
    from app.services.businessplan import list_templates as list_bp_templates

    existing_ids = {t.id for t in list_bp_templates()}

    for branch in ["generic", "pharma"]:
        allowed = get_businessplan_templates_for_branch(branch)
        for tid in allowed:
            assert tid in existing_ids, (
                f"Branche '{branch}' verweist auf nicht existente Template-ID '{tid}'"
            )


# ============================================================ #
# Policy (Datenresidenz + Selbstzuweisung)
# ============================================================ #

def test_jede_userbranch_hat_ein_profil():
    """
    Der wichtigste Test dieser Datei.

    get_industry_profile() faellt bei unbekanntem Code STILL auf generic
    zurueck — und generic erlaubt Cloud. Eine neue Branche im Enum ohne
    _PROFILES-Eintrag liefe also lautlos unreguliert. Dieser Test macht
    aus dem stillen Fallback einen roten Test.
    """
    from app.branches.profiles import _PROFILES

    for branch in UserBranch:
        assert branch.value in _PROFILES, (
            f"UserBranch.{branch.name} hat keinen Eintrag in _PROFILES — "
            f"faellt still auf generic zurueck (allow_cloud_models=True)."
        )


def test_pharma_ist_reguliert():
    assert branch_allows_cloud("pharma") is False
    assert branch_is_self_assignable("pharma") is False
    assert branch_default_model("pharma") == "qwen2.5:7b"


def test_generic_ist_unreguliert():
    assert branch_allows_cloud("generic") is True
    assert branch_is_self_assignable("generic") is True
    assert branch_default_model("generic") is None


def test_default_model_widerspricht_nicht_der_policy():
    """
    Eine Branche ohne Cloud-Erlaubnis darf kein Cloud-Modell als Default
    tragen. Waere ein Widerspruch, den sonst erst der erste User merkt.
    """
    from app.llm.resolver import is_local_model

    for profile in list_industry_profiles():
        if profile.default_model and not profile.allow_cloud_models:
            assert is_local_model(profile.default_model), (
                f"{profile.code}: default_model='{profile.default_model}' ist "
                f"ein Cloud-Modell, aber allow_cloud_models=False"
            )


def test_unbekannte_branche_faellt_auf_generic():
    """Dokumentiert den Fallback bewusst — abgesichert durch den Test oben."""
    assert branch_allows_cloud("automotive") is True


# ============================================================ #
# Guard: PUT /profile/me/branch — Selbstbedienung nur unreguliert
# ============================================================ #

def test_user_darf_nicht_in_regulierte_branche_wechseln(client, user_token):
    """Ein normaler User darf sich nicht selbst zu Pharma machen."""
    r = client.put(
        "/profile/me/branch",
        json={"branch": "pharma"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 403


def test_user_darf_zwischen_freien_branchen_wechseln(client, user_token):
    """generic → generic bleibt erlaubt (self_assignable=True)."""
    r = client.put(
        "/profile/me/branch",
        json={"branch": "generic"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 200


def test_admin_kann_user_in_pharma_setzen(client, admin_token, regular_user):
    """Der Admin-Weg (PATCH /users) muss offen bleiben — sonst Sackgasse."""
    r = client.patch(
        f"/users/{regular_user.id}",
        json={"branch": "pharma"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["branch"] == "pharma"
