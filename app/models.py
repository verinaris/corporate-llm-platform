"""
Datenbank-Modelle.

SQLModel kombiniert SQLAlchemy (DB) + Pydantic (Validierung) in einem.
Eine Klasse beschreibt sowohl die DB-Tabelle als auch das API-Schema.

Aktuell nur das TokenUsage-Modell für Phase 1. In Phase 2 kommen User
und Conversations dazu.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TokenUsage(SQLModel, table=True):
    """
    Loggt jeden LLM-Request mit Token-Verbrauch und Kosten.

    Eine Zeile pro abgeschlossener API-Antwort.
    """

    __tablename__ = "token_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Wer / Was
    user_id: str = Field(default="anonymous", index=True)
    provider: str = Field(index=True)           # "anthropic", "openai", ...
    model: str = Field(index=True)              # "claude-sonnet-4-6", ...

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
