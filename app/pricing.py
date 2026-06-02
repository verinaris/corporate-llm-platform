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

    # Lokale Modelle (Ollama) — laufen auf eigener Hardware → $0
    # (Strom + Hardware-Abschreibung ist Sache des Betreibers)
    "qwen2.5:7b":          (0.00, 0.00),
    "qwen2.5:14b":         (0.00, 0.00),
    "llama3.2:3b":         (0.00, 0.00),
    "llama3.1:8b":         (0.00, 0.00),
    "llama3.1:70b":        (0.00, 0.00),
    "mistral:7b":          (0.00, 0.00),
    "mistral-nemo:12b":    (0.00, 0.00),
    "phi3:3.8b":           (0.00, 0.00),
    "gemma2:9b":           (0.00, 0.00),

    # Fallback für unbekannte Modelle
    "_default": (3.00, 15.00),
}

# Modelle, die garantiert lokal laufen — Pricing = 0
LOCAL_MODEL_PREFIXES = (
    "qwen", "llama", "mistral", "phi", "gemma", "codellama",
    "deepseek", "wizardlm", "vicuna",
)


def is_local_model(model: str) -> bool:
    """Heuristik: lokales Modell (Ollama) oder Cloud-Modell?"""
    return any(model.lower().startswith(p) for p in LOCAL_MODEL_PREFIXES)


def get_pricing(model: str) -> tuple[float, float]:
    """Liefert (input_price, output_price) pro 1M Tokens."""
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    if is_local_model(model):
        return (0.0, 0.0)
    # Ollama-Modelle haben oft `model:version`-Format
    if ":" in model:
        stem = model.split(":", 1)[0]
        for known in MODEL_PRICING:
            if known.startswith(stem + ":"):
                return MODEL_PRICING[known]
    return MODEL_PRICING["_default"]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Berechnet die Kosten eines Requests in USD.

    Beispiel: 1000 Input-Tokens bei Sonnet = 1000 * 3.00 / 1_000_000 = $0.003
    Lokale Modelle: immer 0.0
    """
    input_price, output_price = get_pricing(model)
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    return round(cost, 6)
