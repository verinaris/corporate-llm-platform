"""
Anthropic Claude Client.

Wrappt das offizielle anthropic-SDK und liefert eine LLMResponse im
einheitlichen Format zurück. Unterstützt optional Tool-Use (Multi-Step-Loop).
"""

from typing import Any

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMResponse
from app.schemas import ChatMessage
from app.tools.registry import ToolRegistry


# Schutz gegen Endlos-Loops
MAX_TOOL_ITERATIONS = 5


class AnthropicClient(BaseLLMClient):
    """Implementiert das Base-Interface für Anthropic Claude."""

    provider_name = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        kwargs: dict = {"api_key": settings.anthropic_api_key}
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        self._client = AsyncAnthropic(**kwargs)

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        max_tokens: int,
        tools: list[dict] | None = None,
        tool_registry: ToolRegistry | None = None,
        user_id: int | None = None,
    ) -> LLMResponse:
        """
        Sendet die Nachrichten an Anthropic und gibt Text + Token-Verbrauch zurück.

        Anthropic-Besonderheit: System-Prompts werden über einen separaten
        `system`-Parameter übergeben, nicht in der messages-Liste.

        Tool-Use (optional):
            tools: Liste der verfügbaren Tools im Anthropic-Format
            tool_registry: Die Registry, um Tools auszuführen
            user_id: Für Audit-Logging

        Wenn tools UND tool_registry gesetzt sind, läuft ein Multi-Step-Loop
        (max. 5 Iterationen). LLM kann mehrere Tools nacheinander aufrufen,
        bevor es final antwortet.
        """
        # System-Message herausziehen (Anthropic erwartet sie separat)
        system_prompt: str | None = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        # Token-Akkumulation über alle Iterationen
        total_input_tokens = 0
        total_output_tokens = 0
        final_model = model

        for iteration in range(MAX_TOOL_ITERATIONS):
            # Request bauen
            kwargs: dict = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": chat_messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            if tools:
                kwargs["tools"] = tools

            response = await self._client.messages.create(**kwargs)

            # Token zählen
            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens
            final_model = response.model

            # Falls KEINE Tools genutzt werden: einfacher Pfad
            if not tools or not tool_registry:
                text_parts = [
                    block.text for block in response.content
                    if getattr(block, "type", None) == "text"
                ]
                return LLMResponse(
                    content="".join(text_parts),
                    model=final_model,
                    provider=self.provider_name,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                )

            # Tool-Loop-Logik
            if response.stop_reason == "tool_use":
                # 1. Assistant-Antwort (mit Tool-Calls) zur History hinzufügen
                chat_messages.append({
                    "role": "assistant",
                    "content": [block.model_dump() for block in response.content],
                })

                # 2. Alle Tool-Calls ausführen
                tool_results = []
                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        tool_result = self._execute_tool(
                            tool_registry=tool_registry,
                            tool_name=block.name,
                            tool_input=block.input,
                            tool_use_id=block.id,
                            user_id=user_id,
                        )
                        tool_results.append(tool_result)

                # 3. Tool-Results als User-Message zurück
                chat_messages.append({
                    "role": "user",
                    "content": tool_results,
                })

                # Loop fortsetzen
                continue

            # stop_reason: end_turn / max_tokens / etc. → fertig
            text_parts = [
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            ]
            return LLMResponse(
                content="".join(text_parts),
                model=final_model,
                provider=self.provider_name,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )

        # Loop-Limit erreicht — Notbremse
        return LLMResponse(
            content=(
                "⚠️ Maximales Tool-Iterations-Limit erreicht. "
                "Die Anfrage ist zu komplex für die aktuelle Konfiguration."
            ),
            model=final_model,
            provider=self.provider_name,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
        )

    def _execute_tool(
        self,
        tool_registry: ToolRegistry,
        tool_name: str,
        tool_input: dict,
        tool_use_id: str,
        user_id: int | None,
    ) -> dict[str, Any]:
        """
        Führt ein Tool über die Registry aus und liefert Anthropic-konformes Result.

        Errors werden gefangen und als Error-Result zurückgegeben — der Loop
        bricht NICHT ab, das LLM kann auf Fehler reagieren.
        """
        try:
            result = tool_registry.execute(
                name=tool_name,
                params=tool_input,
                user_id=user_id,
            )
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": str(result),
            }
        except Exception as e:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Tool-Ausführung fehlgeschlagen: {e!s}",
                "is_error": True,
            }
