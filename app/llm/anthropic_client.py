"""
Anthropic Claude Client.

Wrappt das offizielle anthropic-SDK und liefert eine LLMResponse im
einheitlichen Format zurück.
"""

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMResponse
from app.schemas import ChatMessage


class AnthropicClient(BaseLLMClient):
    """Implementiert das Base-Interface für Anthropic Claude."""

    provider_name = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        """
        Sendet die Nachrichten an Anthropic und gibt Text + Token-Verbrauch zurück.

        Anthropic-Besonderheit: System-Prompts werden über einen separaten
        `system`-Parameter übergeben, nicht in der messages-Liste.
        """
        # System-Message herausziehen (Anthropic erwartet sie separat)
        system_prompt: str | None = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        # Request
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self._client.messages.create(**kwargs)

        # Antwort-Content zusammensetzen (Anthropic liefert Content-Blocks)
        text_parts = [
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        content = "".join(text_parts)

        return LLMResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
