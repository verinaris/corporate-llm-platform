"""
API-Schemas (Pydantic).

Definieren die Form der JSON-Anfragen und -Antworten unserer API.
Pydantic validiert eingehende Daten automatisch.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """Eingehende Chat-Anfrage. User wird aus dem JWT-Token bestimmt."""

    messages: list[ChatMessage] = Field(..., min_length=1)
    model: Optional[str] = None
    max_tokens: Optional[int] = None

    # RAG (Phase 3b) — optional. Wenn collection gesetzt, wird die letzte
    # User-Nachricht semantisch in der Sammlung gesucht und der Kontext
    # an Claude mitgegeben.
    collection: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=15)


class SourceReference(BaseModel):
    """Eine Quellenangabe, die in der Antwort verwendet wurde."""

    document_id: int
    filename: str
    page: int
    excerpt: str = Field(description="Kurzer Auszug aus dem Chunk (~200 Zeichen)")
    full_text: str = Field(
        default="",
        description="Vollständiger Chunk-Text für ausführliche Anzeige",
    )
    distance: float = Field(
        description="Kleinerer Wert = relevanter (0.0 = perfekte Übereinstimmung)"
    )


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int


class ChatResponse(BaseModel):
    """Antwort vom LLM samt Metadaten."""

    content: str
    model: str
    provider: str
    usage: UsageInfo
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Bei RAG-Anfragen: verwendete Quellen aus der Sammlung",
    )


# ---------- Stats ----------

class ModelStats(BaseModel):
    requests: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


class UserStats(BaseModel):
    requests: int
    total_tokens: int
    cost_usd: float


class StatsSummary(BaseModel):
    """Gesamtauswertung über alle Requests."""

    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float
    by_model: dict[str, ModelStats]
    by_user: dict[str, UserStats]
