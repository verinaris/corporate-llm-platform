"""
Datenbank-Modelle.

SQLModel kombiniert SQLAlchemy (DB) + Pydantic (Validierung).
"""

from datetime import datetime, timezone
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
