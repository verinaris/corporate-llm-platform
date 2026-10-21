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


# ----------------------------------------------------------------------- #
# Mandantentrennung: Zugriff auf Sammlungen
# ----------------------------------------------------------------------- #
#
# WICHTIG: Fuers LESEN zaehlt NICHT die Rolle, sondern nur die Beziehung zur
# Sammlung (Besitzer, Mitglied, fuer alle lesbar). Admin und Compliance-Officer
# verwalten Rechte, lesen aber keine fremden Inhalte -- gleiches Muster wie
# can_read_audit vs. can_approve: verwalten duerfen ist nicht lesen duerfen.
#
# Analogie: Der Hausmeister hat den Generalschluessel-Kasten, darf aber nicht
# in die Wohnungen. Will er im Notfall hinein, traegt er sich sichtbar ein.

# Rangfolge der Stufen. "owner" ist keine gespeicherte Stufe, sondern ergibt
# sich aus DocumentCollection.created_by.
_COLLECTION_LEVEL_RANK: dict[str, int] = {"read": 1, "maintain": 2, "owner": 3}

# Wer darf Rechte an Sammlungen vergeben/entziehen und "fuer alle" schalten?
_COLLECTION_ACCESS_MANAGERS: frozenset[str] = frozenset({"admin"})


def collection_level(user_email, owner_email, member_level, open_for_all) -> str | None:
    """
    Ermittelt die Stufe eines Users fuer eine Sammlung.

    Returns "owner", "maintain", "read" oder None (kein Zugriff).
    Die hoechste zutreffende Stufe gewinnt.
    """
    if user_email and owner_email and user_email.strip().lower() == owner_email.strip().lower():
        return "owner"
    level = _role_str(member_level) if member_level else None
    if level in ("read", "maintain"):
        return level
    if open_for_all:
        return "read"
    return None


def can_read_collection(level) -> bool:
    """Darf in der Sammlung gesucht / gelesen werden?"""
    return level in _COLLECTION_LEVEL_RANK


def can_maintain_collection(level) -> bool:
    """Darf in der Sammlung hochgeladen, geaendert, geloescht werden?"""
    return _COLLECTION_LEVEL_RANK.get(level or "", 0) >= _COLLECTION_LEVEL_RANK["maintain"]


def can_manage_collection_access(role) -> bool:
    """Darf diese Rolle Rechte an Sammlungen vergeben/entziehen?"""
    return _role_str(role) in _COLLECTION_ACCESS_MANAGERS
