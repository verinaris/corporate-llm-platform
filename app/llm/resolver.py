"""
Modell → Provider. Die eine Wahrheit darüber, welches Modell wo läuft.

Vorher stand diese Information doppelt im Code:
- deklariert als `is_local` in app/api/models.py
- hergeleitet per String-Heuristik in `_resolve_client` in app/api/chat.py

Analogie: Das Nummernschild verrät das Zulassungsland. Man schlägt nicht
in zwei Registern nach — man liest es am Schild ab.

Erweitern: neuen Provider HIER ergänzen, nicht in den Endpoints.
"""

from enum import Enum


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


# Provider, bei denen Daten das eigene Netz verlassen.
# Diese Menge ist die Grundlage jeder Datenresidenz-Policy.
_CLOUD_PROVIDERS = frozenset({Provider.ANTHROPIC})

_OLLAMA_PREFIXES = (
    "llama", "qwen", "mistral", "phi", "gemma", "codellama",
    "deepseek", "wizardlm", "vicuna",
)


class UnknownModelError(ValueError):
    """Modell lässt sich keinem Provider zuordnen."""


def resolve_provider(model: str) -> Provider:
    """
    Ordnet einen Modell-Namen einem Provider zu.

    Raises:
        UnknownModelError: wenn der Name zu keinem Provider passt.
    """
    if model.startswith("claude-"):
        return Provider.ANTHROPIC
    # Ollama-Modelle haben typischerweise das Format `name:tag` (z.B. qwen2.5:7b)
    # ODER sind klar lokale Modelle (llama*, qwen*, mistral*, phi*, gemma*)
    if ":" in model or model.lower().startswith(_OLLAMA_PREFIXES):
        return Provider.OLLAMA
    raise UnknownModelError(
        f"Unbekanntes Modell: '{model}'. "
        f"Cloud-Modelle: 'claude-*'. "
        f"Lokale Modelle: 'qwen2.5:7b', 'llama3.1:8b' usw. (über Ollama)."
    )


def is_local_model(model: str) -> bool:
    """
    True, wenn das Modell auf eigener Hardware läuft — die Daten also
    das Netz nicht verlassen.

    Raises:
        UnknownModelError: wenn der Name zu keinem Provider passt.
    """
    return resolve_provider(model) not in _CLOUD_PROVIDERS
