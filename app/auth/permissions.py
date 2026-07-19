"""
Zentrale Berechtigungs-Logik: wer darf was?

Die eine Wahrheit ueber rollenbasierte Berechtigungen, die quer durch die
App gebraucht werden. Vorher standen sie als Literale in den Endpoints --
eine neue Rolle haette an jeder Pruefstelle nachgezogen werden muessen.

WICHTIG -- zwei getrennte Rechte, die NICHT dasselbe sind:
  - can_read_audit: das DSGVO-Audit-Log lesen (sensible Personendaten)
  - can_approve:    Compliance-/Automations-Antraege freigeben

Sie fallen bei Admin und Compliance-Officer zufaellig zusammen, gehen beim
fachlichen Freigeber (qualified-reviewer) aber auseinander: der darf
freigeben, aber NICHT das Audit-Log einsehen.

Analogie: 'Vertraege gegenzeichnen' und 'Personalakten einsehen' sind zwei
Rechte, auch wenn der Chef beide hat.

Erweitern: neue Rolle in die passende(n) Menge(n) HIER aufnehmen.
"""

# Wer darf das DSGVO-Audit-Log lesen? (sensible Personendaten)
_AUDIT_READERS: frozenset[str] = frozenset({
    "admin",
    "compliance-officer",
})

# Wer darf Compliance-/Automations-Antraege freigeben?
# qualified-reviewer = fachlicher Freigeber (Pharma-QM, Pharmakovigilanz, ...);
# die konkreten Fachgebiete pro Person kommen spaeter als eigenes Modell.
_APPROVERS: frozenset[str] = frozenset({
    "admin",
    "compliance-officer",
    "qualified-reviewer",
})


def _role_str(role) -> str:
    """Normalisiert Enum ODER str auf den reinen String-Wert."""
    return role.value if hasattr(role, "value") else str(role)


def can_read_audit(role) -> bool:
    """Darf diese Rolle das DSGVO-Audit-Log einsehen?"""
    return _role_str(role) in _AUDIT_READERS


def can_approve(role) -> bool:
    """Darf diese Rolle Compliance-/Automations-Antraege freigeben?"""
    return _role_str(role) in _APPROVERS
