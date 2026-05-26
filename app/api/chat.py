"""
Chat-Endpoint (geschützt — Login erforderlich).

Phase 2c: User-Branche → Branchen-Plugin (z.B. Pharma-Disclaimer)
Phase 3b: Optional RAG via 'collection'-Parameter
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.branches import get_plugin
from app.config import get_settings
from app.database import get_session
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import BaseLLMClient
from app.models import User
from app.pricing import calculate_cost
from app.schemas import ChatMessage, ChatRequest, ChatResponse, UsageInfo
from app.services import token_tracker
from app.services.rag import (
    build_rag_context,
    extract_last_user_query,
    inject_rag_context,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _resolve_client(model: str) -> BaseLLMClient:
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
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Sendet eine Chat-Anfrage an das LLM und loggt den Verbrauch."""
    settings = get_settings()
    model = request.model or settings.default_model
    max_tokens = request.max_tokens or settings.default_max_tokens
    client = _resolve_client(model)

    # --- Branchen-Plugin laden ---
    plugin = get_plugin(current_user.branch.value)

    # --- Branchen-System-Prompt vorne anhängen, wenn vorhanden ---
    messages_for_llm: list[ChatMessage] = list(request.messages)
    if branch_prompt := plugin.get_system_prompt():
        messages_for_llm.insert(
            0, ChatMessage(role="system", content=branch_prompt)
        )

    # --- Pre-Process (Phase 3+: PII-Filter) ---
    try:
        messages_for_llm = plugin.pre_process_messages(messages_for_llm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # --- RAG: Wenn Collection gesetzt, Kontext aus Vektor-DB einspielen ---
    sources_for_response = []
    if request.collection:
        query = extract_last_user_query(messages_for_llm)
        if query:
            try:
                context, sources_for_response = build_rag_context(
                    collection=request.collection,
                    query=query,
                    top_k=request.top_k,
                )
                if context:
                    messages_for_llm = inject_rag_context(
                        messages_for_llm, context
                    )
            except Exception as exc:
                # RAG-Fehler nicht fatal — Chat geht ohne Kontext weiter,
                # aber wir loggen das.
                print(f"[RAG] Vektor-Suche fehlgeschlagen: {exc}")

    user_identifier = current_user.email

    # --- LLM-Aufruf ---
    started = time.perf_counter()
    try:
        result = await client.chat(
            messages=messages_for_llm,
            model=model,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        token_tracker.log_usage(
            session,
            user_id=user_identifier,
            provider="anthropic",
            model=model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail=f"LLM-Aufruf fehlgeschlagen: {exc}",
        ) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)

    # --- Post-Process (Disclaimer anhängen, Filter) ---
    result.content = plugin.post_process_response(result.content)

    # --- Logging ---
    token_tracker.log_usage(
        session,
        user_id=user_identifier,
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
            cost_usd=calculate_cost(
                result.model, result.input_tokens, result.output_tokens
            ),
            latency_ms=latency_ms,
        ),
        sources=sources_for_response,
    )
