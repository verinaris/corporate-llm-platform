"""
Abstrakte LLM-Basis-Klasse.

Definiert das Interface, das ALLE LLM-Provider implementieren müssen.
Damit kann der Rest der App provider-agnostisch arbeiten.

Analogie: Eine Steckdose. Egal ob Lampe, Toaster oder Laptop dranhängt —
sie liefert immer 230V. So liefert jeder LLM-Client immer eine
LLMResponse, egal ob Anthropic, OpenAI oder Ollama dahinter steckt.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas import ChatMessage


@dataclass
class LLMResponse:
    """Einheitliche Antwort aller LLM-Clients."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int


class BaseLLMClient(ABC):
    """Interface für LLM-Provider."""

    provider_name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        """Sendet einen Chat-Request und liefert eine vereinheitlichte Antwort."""
        ...
