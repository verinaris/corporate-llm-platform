"""
Zentrale Berechtigungs-Logik: wer darf freigeben?

Die eine Wahrheit darueber, welche Rollen Compliance-Antraege (PendingApproval)
freigeben duerfen. Vorher stand das als Literal im Guard von app/api/admin.py --
eine neue Freigeber-Rolle haette dort und an jeder kuenftigen Pruefstelle
nachgezogen werden muessen.

Analogie: Eine Tuersteher-Liste an EINER Tuer, nicht an jeder Wand ein Zettel.

Erweitern: neue freigabeberechtigte Rolle HIER in _APPROVER_ROLES ergaenzen,
nicht in den Endpoints.
"""

# Rollen, die Compliance-Freigaben erteilen duerfen.
# Reihenfolge egal; die Menge ist die Autoritaet.
_APPROVER_ROLES: frozenset[str] = frozenset({
    "admin",
    "compliance-officer",
})


def _role_str(role) -> str:
    """Normalisiert Enum ODER str auf den reinen String-Wert."""
    return role.value if hasattr(role, "value") else str(role)


def can_approve(role) -> bool:
    """
    Darf diese Rolle Compliance-Antraege freigeben?

    Akzeptiert UserRole-Enum oder String.
    """
    return _role_str(role) in _APPROVER_ROLES
