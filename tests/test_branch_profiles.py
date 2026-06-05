"""Tests für das zentrale Branchen-Profil-System."""

import pytest

from app.branches.profiles import (
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
