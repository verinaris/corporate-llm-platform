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

    # Tool-Use (Phase 7a)
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"
    TOOL_DENIED = "tool_denied"
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


# =====================================================================
# Phase 7a: ApprovalToken für sensitive Tool-Calls
# =====================================================================

class ApprovalToken(SQLModel, table=True):
    """
    Freigabe-Token für sensitive Tool-Aufrufe (Compliance-Vier-Augen-Prinzip).

    Ein Compliance-Officer generiert einen Token für einen konkreten
    Tool-Aufruf eines Users. Der Token ist 15 Minuten gültig und kann
    genau EINMAL verwendet werden.

    Analogie: Wie ein Kinoticket — kurze Gültigkeit, ein Film, dann entwertet.
    """

    __tablename__ = "approval_token"

    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True, description="Zufälliger Token-String")

    # Wer beantragt den Call?
    requester_email: str = Field(index=True)
    requester_role: str

    # Welcher Tool-Call soll freigegeben werden?
    tool_name: str = Field(index=True)
    params_hash: str = Field(
        description="SHA256 der Params — verhindert Token-Missbrauch für andere Aufrufe"
    )

    # Wer hat freigegeben?
    approver_email: str
    approver_role: str

    # Zeit-Fenster
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="Token verfällt automatisch")

    # Status
    used: bool = Field(default=False, description="Wurde der Token schon verbraucht?")
    used_at: datetime | None = Field(default=None)


# =====================================================================
# Phase 7b: PendingApproval fuer Compliance-Dashboard
# =====================================================================

class ApprovalStatus(str, Enum):
    """Status eines Approval-Antrags."""
    PENDING = "pending"          # Wartet auf Compliance-Entscheidung
    APPROVED = "approved"         # Freigegeben, Token wurde ausgestellt
    REJECTED = "rejected"         # Abgelehnt
    EXPIRED = "expired"           # Zu lange nicht bearbeitet


class PendingApproval(SQLModel, table=True):
    """
    Anfrage eines Users auf Tool-Ausfuehrung mit Vier-Augen-Prinzip.

    Wenn ein User ein sensitives Tool aufruft (requires_human_oversight=True),
    wird ein PendingApproval erstellt. Compliance-Officer sieht diese im
    Dashboard und kann Approve oder Reject klicken.

    Analogie: Wie ein Antrag im Postfach eines Vorgesetzten.
    """

    __tablename__ = "pending_approval"

    id: int | None = Field(default=None, primary_key=True)

    # Wer stellt den Antrag?
    requester_email: str = Field(index=True)
    requester_role: str

    # Was soll ausgefuehrt werden?
    tool_name: str = Field(index=True)
    params_json: str = Field(description="JSON-Serialisierung der Tool-Params")
    params_hash: str = Field(description="SHA256 der Params (fuer Token-Bindung)")

    # Optional: Kontext/Begruendung des Users
    reason: str | None = Field(default=None)

    # Wer hat entschieden?
    decided_by_email: str | None = Field(default=None)
    decided_by_role: str | None = Field(default=None)
    decision_notes: str | None = Field(default=None)

    # Zeit-Fenster
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = Field(default=None)

    # Status
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, index=True)

    # Verknüpfung zum ausgestellten Token (falls approved)
    approval_token: str | None = Field(default=None)
