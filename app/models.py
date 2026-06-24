"""
Datenbank-Modelle.

SQLModel kombiniert SQLAlchemy (DB) + Pydantic (Validierung).
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


# ============================================================ #
# Enums
# ============================================================ #

class UserRole(str, Enum):
    """Globale Rolle eines Users (orthogonal zur Branche)."""

    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance-officer"
    PHARMA_REFERENT = "pharma-referent"
    USER = "user"


class UserBranch(str, Enum):
    """
    Branchen-Profil eines Users.

    Dieses Feld ist der **zentrale Schalter** für die gesamte Plattform:
    - Pharma-Plugin im Chat wird aktiviert/deaktiviert
    - Businessplan-Modul zeigt passende Vorlagen
    - Industry-Checks (Phase 5b) werden getriggert
    - (später) Agenten-Vorlagen werden gefiltert

    Erweitern: neuen Wert hier + Mapping in
    app/branches/profiles.py ergänzen.
    """

    GENERIC = "generic"
    PHARMA = "pharma"             # = Pharma-Beratung & Vertrieb
    # später: LEGAL, TAX, ENERGY, CRAFT, MEDICAL


# ============================================================ #
# Tabellen
# ============================================================ #

class User(SQLModel, table=True):
    """Anwendungs-User. Authentifizierung via E-Mail + Passwort."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str

    role: UserRole = Field(default=UserRole.USER, index=True)
    branch: UserBranch = Field(default=UserBranch.GENERIC, index=True)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TokenUsage(SQLModel, table=True):
    """Loggt jeden LLM-Request mit Token-Verbrauch und Kosten."""

    __tablename__ = "token_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )

    # Wer / Was
    user_id: str = Field(default="anonymous", index=True)
    provider: str = Field(index=True)
    model: str = Field(index=True)

    # Token-Zahlen
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Kosten in USD
    cost_usd: float = 0.0

    # Performance
    latency_ms: int = 0

    # Status
    success: bool = True
    error: Optional[str] = None


class Document(SQLModel, table=True):
    """
    Dokument-Metadaten (Phase 3a).

    Die eigentlichen Chunks + Embeddings liegen in ChromaDB.
    Diese Tabelle speichert die "Header-Info" jedes hochgeladenen Files.
    """

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    collection: str = Field(index=True)         # z.B. "pharma-fachinfos"
    original_filename: str
    content_type: str = "application/pdf"
    size_bytes: int = 0
    page_count: int = 0
    chunk_count: int = 0
    uploaded_by: str = Field(index=True)        # User-E-Mail
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    # Pfad zur Original-Datei auf Disk (nicht in ChromaDB)
    stored_path: Optional[str] = None
    # SHA-256 Hash der Datei-Bytes (Phase 3c+) — für Duplikatsprüfung
    # pro Sammlung. Bestehende Dokumente vor diesem Feature haben None.
    content_hash: Optional[str] = Field(default=None, index=True)


class DocumentCollection(SQLModel, table=True):
    """
    Metadaten einer Dokumenten-Sammlung (Phase 3c).

    Sammlungen sind bisher nur Strings (siehe Document.collection).
    Diese Tabelle fügt optionale Beschreibung + Tags hinzu — wichtig
    für Multi-Tenant-Setups und für klare Auffindbarkeit im UI.
    """

    __tablename__ = "document_collections"

    name: str = Field(primary_key=True, index=True)
    description: Optional[str] = Field(default=None)
    tags: str = Field(default="")  # komma-separiert
    created_by: str = Field(index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================ #
# Audit-Log (Phase 6a — Compliance)
# ============================================================ #

class AuditAction(str, Enum):
    """
    Auditierte Aktionen.

    Wir loggen nur Aktionen mit Compliance-Relevanz, NICHT jeden API-Call.
    Faustregel: Wenn ein DSB nachfragt "wer hat wann was getan?" — diese
    Aktionen muss man beantworten können.
    """

    # Auth
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    # User-Management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    BRANCH_CHANGED = "branch_changed"

    # Daten-Operationen
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    COLLECTION_CREATED = "collection_created"
    COLLECTION_DELETED = "collection_deleted"

    # Chat / LLM
    CHAT_QUERY = "chat_query"

    # Businessplan
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    PLAN_DELETED = "plan_deleted"
    PLAN_EXPORTED = "plan_exported"

    # DSGVO
    USER_DATA_EXPORT = "user_data_export"      # Art. 15: Auskunftsrecht
    USER_FULL_DELETE = "user_full_delete"      # Art. 17: Vergessen werden


class AuditLog(SQLModel, table=True):
    """
    Audit-Trail für alle compliance-relevanten Aktionen.

    **DSGVO-Strategie bei User-Löschung (Art. 17):**
    User-PII (E-Mail, Name) werden im User-Datensatz gelöscht, aber der
    Audit-Trail-Eintrag bleibt mit `user_email` = "deleted_user_<id>"
    pseudonymisiert. So bleibt die gesetzliche Aufbewahrungspflicht
    (z.B. 10 Jahre für Pharma/Steuer) erfüllt, ohne dass die Identität
    wiederherstellbar ist.

    **Retention:** Standard 10 Jahre (Pharma-konform). Konfigurierbar
    via Settings, automatisches Lösch-Skript siehe Phase 6c.
    """

    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Wer
    user_email: str = Field(index=True)        # ggf. pseudonymisiert
    user_role: str = Field(default="unknown")  # zum Zeitpunkt der Aktion

    # Was
    action: AuditAction = Field(index=True)
    target_type: Optional[str] = Field(default=None, index=True)  # "document", "plan", ...
    target_id: Optional[str] = Field(default=None, index=True)    # z.B. doc-ID

    # Kontext (frei strukturierbar als JSON-String)
    details: Optional[str] = Field(default=None)  # JSON oder Klartext

    # Technisch
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)

    # Ergebnis
    success: bool = Field(default=True, index=True)


# ====================================== #
# Trial / Lizenz
# ====================================== #


class TrialState(SQLModel, table=True):
    """
    Verfolgt das Installations-Datum und Lizenz-Status der Verinaris-Instanz.

    Wichtig: Diese Tabelle enthält IMMER nur 1 Zeile — sie repräsentiert die
    gesamte Installation (nicht einzelne User). Beim ersten App-Start wird
    die Zeile automatisch angelegt.

    Felder:
        installed_at: Wann wurde die App das erste Mal gestartet?
        expires_at: Trial-Ende (= installed_at + 7 Tage)
        license_key: Optional — für Phase 2 vorbereitet
        license_valid_until: Optional — Ablaufdatum der Lizenz
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    installed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Erster App-Start (UTC)",
    )
    expires_at: datetime = Field(
        description="Trial-Ende (installed_at + 7 Tage)",
    )
    license_key: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Lizenz-Schlüssel (Phase 2)",
    )
    license_valid_until: Optional[datetime] = Field(
        default=None,
        description="Ablaufdatum der aktiven Lizenz",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Freie Notizen (z.B. 'Initial installation')",
    )
