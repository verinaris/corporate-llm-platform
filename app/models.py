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
    """Branchenmodul-Zuordnung. Steuert das aktive Plugin."""

    GENERIC = "generic"
    PHARMA = "pharma"
    # später: LEGAL, TAX, MEDICAL, CRAFT


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
