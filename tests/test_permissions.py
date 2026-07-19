"""
Tests fuer app/auth/permissions.py — die zwei getrennten Rechte.

Der wichtigste Test ist test_qualified_reviewer_darf_freigeben_aber_nicht_lesen:
Er sichert die Zwecktrennung ab. Faellt sie (z.B. weil jemand can_approve und
can_read_audit wieder zusammenlegt), wird er rot.
"""

import pytest

from app.auth.permissions import can_approve, can_read_audit
from app.models import UserRole


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER])
def test_admin_und_compliance_duerfen_beides(role):
    assert can_approve(role) is True
    assert can_read_audit(role) is True


def test_qualified_reviewer_darf_freigeben_aber_nicht_lesen():
    """Die Zwecktrennung: freigeben ja, Audit-Log nein."""
    assert can_approve(UserRole.QUALIFIED_REVIEWER) is True
    assert can_read_audit(UserRole.QUALIFIED_REVIEWER) is False


@pytest.mark.parametrize("role", [UserRole.PHARMA_REFERENT, UserRole.USER])
def test_normale_rollen_duerfen_nichts(role):
    assert can_approve(role) is False
    assert can_read_audit(role) is False


def test_akzeptiert_string_und_enum():
    assert can_approve("qualified-reviewer") is True
    assert can_approve(UserRole.QUALIFIED_REVIEWER) is True
    assert can_read_audit("qualified-reviewer") is False
