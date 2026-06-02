"""
Models-API (Phase 4).

Liefert die Liste verfügbarer Modelle pro Provider:
- Anthropic: hardcoded Liste aus pricing.py
- Ollama: dynamisch vom lokalen Server abgefragt

Streamlit nutzt das, um das Modell-Dropdown dynamisch zu befüllen.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.llm.ollama_client import list_installed_models
from app.models import User

router = APIRouter(prefix="/models", tags=["models"])


# ============================================================ #
# Schemas
# ============================================================ #

class ModelInfo(BaseModel):
    id: str = Field(description="Modell-Identifier für API-Aufrufe")
    label: str = Field(description="Schöner Name für die UI")
    provider: str
    is_local: bool = Field(
        description="True wenn das Modell auf eigener Hardware läuft (Ollama)"
    )
    notes: Optional[str] = None


class ProviderInfo(BaseModel):
    name: str
    available: bool = True
    models: list[ModelInfo] = Field(default_factory=list)
    note: Optional[str] = None


class AvailableModelsResponse(BaseModel):
    providers: list[ProviderInfo]
    default_model: str


# ============================================================ #
# Anthropic — feste Liste
# ============================================================ #

_ANTHROPIC_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="claude-haiku-4-5",
        label="Haiku 4.5  ·  schnell & günstig",
        provider="anthropic",
        is_local=False,
        notes="Niedrige Latenz, $1/M input · $5/M output",
    ),
    ModelInfo(
        id="claude-sonnet-4-6",
        label="Sonnet 4.6  ·  ausgewogen (Default)",
        provider="anthropic",
        is_local=False,
        notes="Sweet-Spot Preis/Leistung, $3/M input · $15/M output",
    ),
    ModelInfo(
        id="claude-opus-4-7",
        label="Opus 4.7  ·  stärkstes Modell",
        provider="anthropic",
        is_local=False,
        notes="Höchste Qualität, $15/M input · $75/M output",
    ),
]


def _label_for_ollama(model_id: str, size_bytes: int) -> str:
    """Macht einen User-freundlichen Label aus dem Ollama-Modell-Namen."""
    size_gb = size_bytes / (1024 ** 3) if size_bytes else 0
    pretty = model_id
    if size_gb:
        return f"{pretty}  ·  lokal ({size_gb:.1f} GB)"
    return f"{pretty}  ·  lokal"


# ============================================================ #
# Endpoint
# ============================================================ #

@router.get("/available", response_model=AvailableModelsResponse)
async def get_available_models(
    user: User = Depends(get_current_user),
) -> AvailableModelsResponse:
    """
    Liefert alle aktuell nutzbaren Modelle, gruppiert nach Provider.

    Anthropic ist statisch. Ollama-Modelle werden live vom Server abgefragt
    — wenn Ollama nicht läuft, fällt das einfach weg (kein Fehler).
    """
    settings = get_settings()

    providers: list[ProviderInfo] = []

    # Anthropic
    providers.append(
        ProviderInfo(
            name="anthropic",
            available=bool(settings.anthropic_api_key),
            models=_ANTHROPIC_MODELS,
            note=(
                None if settings.anthropic_api_key
                else "ANTHROPIC_API_KEY fehlt in .env"
            ),
        )
    )

    # Ollama — dynamisch
    ollama_models = await list_installed_models()
    ollama_provider = ProviderInfo(
        name="ollama",
        available=bool(ollama_models),
        note=(
            None if ollama_models
            else (
                f"Kein Ollama-Server unter {settings.ollama_base_url} erreichbar. "
                f"Starte: `ollama serve`"
            )
        ),
    )
    for entry in ollama_models:
        ollama_provider.models.append(
            ModelInfo(
                id=entry["name"],
                label=_label_for_ollama(entry["name"], entry["size_bytes"]),
                provider="ollama",
                is_local=True,
                notes="Lokal auf eigener Hardware — keine API-Kosten",
            )
        )
    providers.append(ollama_provider)

    return AvailableModelsResponse(
        providers=providers,
        default_model=settings.default_model,
    )
