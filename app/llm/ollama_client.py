"""
Ollama-Client (Phase 4).

Spricht mit einem lokalen Ollama-Server (Standard: http://localhost:11434).
Ollama läuft auf dem Mac (oder einem anderen Rechner im Netz) und stellt
beliebige Open-Source-Modelle zur Verfügung (Llama, Qwen, Mistral, ...).

Vorteile gegenüber Cloud-APIs:
- 100% lokal — keine Daten verlassen das Gerät
- Keine API-Kosten
- Funktioniert offline
- Datenschutzfreundlich (besonders für Pharma/Recht/Steuer)

Nachteile:
- Modelle sind meist kleiner / weniger fähig als Frontier-Cloud-Modelle
- Latenz hängt von eigener Hardware ab
- Modelle müssen lokal heruntergeladen werden

Analogie: Eigene Hauseigenes Kraftwerk vs. Stromnetz-Anschluss.
Eigenständig + sicher, aber begrenztere Kapazität.
"""

import httpx

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMResponse
from app.schemas import ChatMessage


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
    ) -> LLMResponse:
        """
        Sendet die Nachrichten an Ollama und gibt Text + Token-Verbrauch zurück.

        Ollama unterstützt die System-Message direkt in der messages-Liste —
        wir können sie einfach durchreichen.
        """
        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            },
        }

        # Lange Timeout, weil das Modell evtl. erst geladen werden muss
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
                f"Modell '{model}' ist auf dem Ollama-Server nicht verfügbar. "
                f"Bitte ziehen mit: `ollama pull {model}`"
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Ollama-Fehler [{response.status_code}]: {response.text}"
            )

        data = response.json()

        content = (data.get("message") or {}).get("content", "")
        input_tokens = int(data.get("prompt_eval_count", 0))
        output_tokens = int(data.get("eval_count", 0))

        return LLMResponse(
            content=content,
            model=data.get("model", model),
            provider=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


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
