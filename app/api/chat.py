"""
Chat-Endpoint (geschützt — Login erforderlich).

Phase 2c: User-Branche → Branchen-Plugin (z.B. Pharma-Disclaimer)
Phase 3b: Optional RAG via 'collection'-Parameter
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.branches import get_plugin
from app.branches.profiles import get_industry_profile
from app.config import get_settings
from app.database import get_session
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import BaseLLMClient
from app.llm.ollama_client import OllamaClient
from app.llm.resolver import (
    Provider,
    UnknownModelError,
    is_local_model,
    resolve_provider,
)
from app.models import AuditAction, User
from app.pricing import calculate_cost
from app.schemas import ChatMessage, ChatRequest, ChatResponse, UsageInfo
from app.services import audit, token_tracker
from app.services.rag import (
    build_rag_context,
    extract_last_user_query,
    inject_rag_context,
)
from app.tools.registry import ApprovalPendingError, ToolRegistry

router = APIRouter(prefix="/chat", tags=["chat"])


def _resolve_client(model: str) -> BaseLLMClient:
    """
    Liefert den Client zum Modell.

    Die Zuordnung Modell → Provider steht in app/llm/resolver.py — hier
    wird sie nur noch in einen HTTP-Status übersetzt.
    """
    try:
        provider = resolve_provider(model)
    except UnknownModelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if provider is Provider.ANTHROPIC:
        return AnthropicClient()
    return OllamaClient()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Sendet eine Chat-Anfrage an das LLM und loggt den Verbrauch."""
    settings = get_settings()
    profile = get_industry_profile(current_user.branch)
    user_role = current_user.role.value if current_user.role else "user"

    # Branchen-Default vor globalem Default: sonst laeuft ein Pharma-User
    # ohne eigene Modellwahl in die eigene Sperre.
    model = request.model or profile.default_model or settings.default_model
    max_tokens = request.max_tokens or settings.default_max_tokens
    client = _resolve_client(model)  # 400 bei unbekanntem Modell

    # --- Datenresidenz-Policy (harte Kontrolle) ------------------------ #
    # Ein gefiltertes Dropdown ist Kosmetik -- per curl geht es daran
    # vorbei. Die Entscheidung faellt hier oder nirgends.
    if not profile.allow_cloud_models and not is_local_model(model):
        audit.log(
            user_email=current_user.email,
            action=AuditAction.MODEL_DENIED,
            user_role=user_role,
            target_type="model",
            target_id=model,
            details={
                "branch": profile.code,
                "reason": "cloud_model_blocked",
                "suggested_model": profile.default_model,
            },
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            success=False,
            session=session,
        )
        hinweis = (
            f" Bitte ein lokales Modell waehlen, z.B. '{profile.default_model}'."
            if profile.default_model
            else " Bitte ein lokales Modell waehlen."
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Die Branche '{profile.short_name}' erlaubt keine Cloud-Modelle. "
                f"Das Modell '{model}' wuerde Daten an einen externen Anbieter "
                f"senden.{hinweis}"
            ),
        )

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

    # --- Tool-Use: Tools fuer User-Rolle aus Registry laden ---
    available_tools = ToolRegistry.get_for_role(user_role)
    tools_for_llm = (
        [t.to_anthropic_format() for t in available_tools]
        if available_tools
        else None
    )

    # --- LLM-Aufruf ---
    started = time.perf_counter()
    try:
        result = await client.chat(
            messages=messages_for_llm,
            model=model,
            max_tokens=max_tokens,
            tools=tools_for_llm,
            tool_registry=ToolRegistry if tools_for_llm else None,
            user_id=current_user.id,
        )
    except ApprovalPendingError as exc:
        # Sensitives Tool -> Antrag angelegt, User informieren
        latency_ms = int((time.perf_counter() - started) * 1000)
        token_tracker.log_usage(
            session,
            user_id=user_identifier,
            provider=client.provider_name,
            model=model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error="approval_pending",
        )
        # 202 Accepted = "angenommen, wird bearbeitet"
        raise HTTPException(
            status_code=202,
            detail={
                "status": "approval_pending",
                "message": (
                    f"Der Vorgang fuer Tool '{exc.tool_name}' "
                    f"wurde als Antrag Nr. {exc.request_id} eingereicht. "
                    "Ein Compliance-Officer wird die Freigabe pruefen. "
                    "Sie koennen den Status unter 'Freigaben' verfolgen."
                ),
                "request_id": exc.request_id,
                "tool_name": exc.tool_name,
            },
        ) from exc
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        token_tracker.log_usage(
            session,
            user_id=user_identifier,
            provider=client.provider_name,
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
