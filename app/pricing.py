"""
Preistabelle für LLM-Modelle.

Wird vom TokenTracker genutzt, um pro Request die Kosten zu berechnen.
Preise sind in USD pro 1.000.000 Tokens (Stand: 2026).

Hinweis: Preise sind Schätzwerte und können sich ändern. Für reale
Produktion: regelmäßig gegen offizielle Preisseiten abgleichen.
"""

# Preise: (input_per_million, output_per_million) in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # Anthropic — Claude 4-Familie
    "claude-opus-4-7":          (15.00, 75.00),
    "claude-opus-4-6":          (15.00, 75.00),
    "claude-sonnet-4-6":        ( 3.00, 15.00),
    "claude-haiku-4-5":         ( 1.00,  5.00),
    "claude-haiku-4-5-20251001":( 1.00,  5.00),

    # Fallback für unbekannte Modelle
    "_default": (3.00, 15.00),
}


def get_pricing(model: str) -> tuple[float, float]:
    """Liefert (input_price, output_price) pro 1M Tokens."""
    return MODEL_PRICING.get(model, MODEL_PRICING["_default"])


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Berechnet die Kosten eines Requests in USD.

    Beispiel: 1000 Input-Tokens bei Sonnet = 1000 * 3.00 / 1_000_000 = $0.003
    """
    input_price, output_price = get_pricing(model)
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    return round(cost, 6)
