"""
Chat-Endpoint.

Nimmt eine Liste Messages entgegen, leitet sie an den passenden
LLM-Provider weiter und loggt den Token-Verbrauch in die DB.
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import BaseLLMClient
from app.pricing import calculate_cost
from app.schemas import ChatRequest, ChatResponse, UsageInfo
from app.services import token_tracker

router = APIRouter(prefix="/chat", tags=["chat"])


# In Phase 1 nur Anthropic — in Phase 4 wird das ein Provider-Registry
def _resolve_client(model: str) -> BaseLLMClient:
    """Wählt den passenden Client anhand des Modellnamens."""
    if model.startswith("claude-"):
        return AnthropicClient()
    raise HTTPException(
        status_code=400,
        detail=f"Unbekanntes Modell: {model}. Aktuell nur 'claude-*' unterstützt.",
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    """Sendet eine Chat-Anfrage an das LLM und loggt den Verbrauch."""
    settings = get_settings()
    model = request.model or settings.default_model
    max_tokens = request.max_tokens or settings.default_max_tokens
    client = _resolve_client(model)

    started = time.perf_counter()
    try:
        result = await client.chat(
            messages=request.messages,
            model=model,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # breit, damit wir den Fehler auch loggen können
        latency_ms = int((time.perf_counter() - started) * 1000)
        token_tracker.log_usage(
            session,
            user_id=request.user_id or "anonymous",
            provider="anthropic",
            model=model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail=f"LLM-Aufruf fehlgeschlagen: {exc}") from exc

    latency_ms = int((time.perf_counter() - started) * 1000)

    token_tracker.log_usage(
        session,
        user_id=request.user_id or "anonymous",
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=latency_ms,
        success=True,
    )

    return ChatResponse(
        content=result.content,
        model=result.model,
        provider=result.provider,
        usage=UsageInfo(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.input_tokens + result.output_tokens,
            cost_usd=calculate_cost(result.model, result.input_tokens, result.output_tokens),
            latency_ms=latency_ms,
        ),
    )
