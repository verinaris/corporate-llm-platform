"""
Ollama-Client (Phase 4 + Phase 7a Tool-Use).

Spricht mit einem lokalen Ollama-Server (Standard: http://localhost:11434).

Vorteile gegenüber Cloud-APIs:
- 100% lokal — keine Daten verlassen das Gerät
- Keine API-Kosten
- Funktioniert offline
- Datenschutzfreundlich (Pharma/Recht/Steuer)

Tool-Use: Ab qwen2.5, llama3.1 nativ unterstützt.
"""

import json

import httpx

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMResponse
from app.schemas import ChatMessage
from app.tools.registry import ToolRegistry


# Schutz gegen Endlos-Loops
MAX_TOOL_ITERATIONS = 5


class OllamaClient(BaseLLMClient):
    """Implementiert das Base-Interface für einen lokalen Ollama-Server."""

    provider_name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")

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
        Sendet die Nachrichten an Ollama und gibt Text + Token-Verbrauch zurück.

        Tool-Use (optional): Wenn tools UND tool_registry gesetzt sind, läuft
        ein Multi-Step-Loop (max. 5 Iterationen). Modell muss Tool-Use
        unterstützen (qwen2.5, llama3.1, etc.).
        """
        chat_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Token-Akkumulation über alle Iterationen
        total_input_tokens = 0
        total_output_tokens = 0

        for iteration in range(MAX_TOOL_ITERATIONS):
            payload = {
                "model": model,
                "messages": chat_messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                },
            }
            if tools:
                # Ollama nutzt Anthropic-ähnliches Format, aber mit "function"-Wrapper
                payload["tools"] = self._convert_tools_to_ollama(tools)

            data = await self._call_ollama(payload)

            # Token zählen
            total_input_tokens += int(data.get("prompt_eval_count", 0))
            total_output_tokens += int(data.get("eval_count", 0))

            message = data.get("message") or {}
            content = message.get("content", "")
            tool_calls = message.get("tool_calls") or []

            # Falls KEINE Tools genutzt werden ODER keine Tool-Calls kamen:
            # Fertige Antwort
            if not tools or not tool_registry or not tool_calls:
                return LLMResponse(
                    content=content,
                    model=data.get("model", model),
                    provider=self.provider_name,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                )

            # Tool-Loop
            # 1. Assistant-Message (mit Tool-Calls) zur History
            chat_messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            # 2. Tool-Calls ausführen
            for call in tool_calls:
                fn = call.get("function", {})
                tool_name = fn.get("name", "")
                # Ollama liefert arguments manchmal als String, manchmal als Dict
                raw_args = fn.get("arguments", {})
                if isinstance(raw_args, str):
                    try:
                        tool_input = json.loads(raw_args)
                    except json.JSONDecodeError:
                        tool_input = {}
                else:
                    tool_input = raw_args

                result_str = self._execute_tool(
                    tool_registry=tool_registry,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    user_id=user_id,
                )

                # 3. Tool-Result als "tool"-Message zurück
                chat_messages.append({
                    "role": "tool",
                    "content": result_str,
                })

            # Loop fortsetzen
            continue

        # Loop-Limit erreicht — Notbremse
        return LLMResponse(
            content=(
                "⚠️ Maximales Tool-Iterations-Limit erreicht. "
                "Die Anfrage ist zu komplex für die aktuelle Konfiguration."
            ),
            model=model,
            provider=self.provider_name,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
        )

    async def _call_ollama(self, payload: dict) -> dict:
        """HTTP-Call zum Ollama-Server mit Error-Handling."""
        async with httpx.AsyncClient(timeout=300) as http:
            try:
                response = await http.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"Ollama-Server nicht erreichbar unter {self._base_url}. "
                    f"Läuft `ollama serve`? Original-Fehler: {exc}"
                ) from exc

        if response.status_code == 404:
            raise RuntimeError(
                f"Modell '{payload.get('model')}' ist auf dem Ollama-Server "
                f"nicht verfügbar. Bitte ziehen mit: "
                f"`ollama pull {payload.get('model')}`"
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Ollama-Fehler [{response.status_code}]: {response.text}"
            )

        return response.json()

    def _convert_tools_to_ollama(self, tools: list[dict]) -> list[dict]:
        """
        Konvertiert Anthropic-Tool-Format zu Ollama-Tool-Format.

        Anthropic: {"name": ..., "description": ..., "input_schema": {...}}
        Ollama:    {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
        """
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return ollama_tools

    def _execute_tool(
        self,
        tool_registry: ToolRegistry,
        tool_name: str,
        tool_input: dict,
        user_id: int | None,
    ) -> str:
        """
        Führt ein Tool aus. Result wird als String zurückgegeben (Ollama-Format).
        Errors werden gefangen und als Error-String zurückgegeben.
        """
        try:
            result = tool_registry.execute(
                name=tool_name,
                params=tool_input,
                user_id=user_id,
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Tool-Ausführung fehlgeschlagen: {e!s}",
            }, ensure_ascii=False)


# ----------------------------------------------------------------------- #
# Helper: verfügbare Modelle vom lokalen Ollama abfragen
# ----------------------------------------------------------------------- #

async def list_installed_models() -> list[dict]:
    """
    Fragt den lokalen Ollama-Server nach installierten Modellen.

    Liefert eine Liste von Dicts mit {name, size_bytes, modified_at}.
    Bei Fehlern (Ollama nicht erreichbar): leere Liste.
    """
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=5) as http:
        try:
            r = await http.get(f"{base_url}/api/tags")
        except httpx.RequestError:
            return []

    if r.status_code != 200:
        return []

    data = r.json()
    models = []
    for entry in data.get("models", []):
        models.append({
            "name": entry.get("name", ""),
            "size_bytes": entry.get("size", 0),
            "modified_at": entry.get("modified_at", ""),
        })
    return models
