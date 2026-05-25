"""
Token-Tracker.

Loggt jeden LLM-Request in die DB (Tabelle `token_usage`) und stellt
Auswertungsfunktionen bereit.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models import TokenUsage
from app.pricing import calculate_cost
from app.schemas import ModelStats, StatsSummary, UserStats


def log_usage(
    session: Session,
    *,
    user_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    success: bool = True,
    error: Optional[str] = None,
) -> TokenUsage:
    """Schreibt einen Token-Usage-Eintrag in die DB."""
    cost = calculate_cost(model, input_tokens, output_tokens)
    record = TokenUsage(
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        success=success,
        error=error,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_summary(
    session: Session,
    user_filter: Optional[str] = None,
) -> StatsSummary:
    """
    Liefert eine Auswertung über die Requests.

    Wenn user_filter gesetzt ist, werden nur Einträge dieses Users aggregiert.
    """
    query = select(TokenUsage)
    if user_filter:
        query = query.where(TokenUsage.user_id == user_filter)
    rows = session.exec(query).all()

    total_requests = len(rows)
    total_input = sum(r.input_tokens for r in rows)
    total_output = sum(r.output_tokens for r in rows)
    total_cost = round(sum(r.cost_usd for r in rows), 6)

    # by_model
    model_agg: dict[str, dict] = defaultdict(
        lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    )
    for r in rows:
        m = model_agg[r.model]
        m["requests"] += 1
        m["input_tokens"] += r.input_tokens
        m["output_tokens"] += r.output_tokens
        m["cost_usd"] += r.cost_usd

    by_model = {
        model: ModelStats(
            requests=v["requests"],
            input_tokens=v["input_tokens"],
            output_tokens=v["output_tokens"],
            cost_usd=round(v["cost_usd"], 6),
        )
        for model, v in model_agg.items()
    }

    # by_user
    user_agg: dict[str, dict] = defaultdict(
        lambda: {"requests": 0, "total_tokens": 0, "cost_usd": 0.0}
    )
    for r in rows:
        u = user_agg[r.user_id]
        u["requests"] += 1
        u["total_tokens"] += r.total_tokens
        u["cost_usd"] += r.cost_usd

    by_user = {
        user: UserStats(
            requests=v["requests"],
            total_tokens=v["total_tokens"],
            cost_usd=round(v["cost_usd"], 6),
        )
        for user, v in user_agg.items()
    }

    return StatsSummary(
        total_requests=total_requests,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_cost_usd=total_cost,
        by_model=by_model,
        by_user=by_user,
    )
