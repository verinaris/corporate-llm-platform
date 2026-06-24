"""
CalculateDateTool — Berechnet Datumsangaben aus natürlichsprachigen Ausdrücken.

Beispiele:
- "in 6 Wochen ab heute"
- "letzter Tag des Monats"
- "30 Tage ab 15.06.2026"

Wird vom LLM aufgerufen, wenn Fristen oder Termine berechnet werden müssen.
"""

from datetime import date, timedelta
from typing import Any

from app.tools.base import BaseTool


class CalculateDateTool(BaseTool):
    """Berechnet Datumsangaben (z.B. Fristen, Termine)."""

    name = "calculate_date"
    description = (
        "Berechnet ein Datum basierend auf einem Basis-Datum und einer "
        "Anzahl von Tagen, Wochen oder Monaten. Nützlich für Fristen "
        "und Termin-Planung."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "base_date": {
                "type": "string",
                "format": "date",
                "description": "Basis-Datum im ISO-Format (YYYY-MM-DD). Default: heute.",
            },
            "days": {
                "type": "integer",
                "description": "Anzahl Tage hinzufügen (negativ = subtrahieren).",
            },
            "weeks": {
                "type": "integer",
                "description": "Anzahl Wochen hinzufügen (wird in Tage umgerechnet).",
            },
        },
        "required": [],
    }

    # Konfiguration
    requires_human_oversight = False  # Mathematik ist harmlos
    allowed_roles = ["admin", "compliance-officer", "pharma-referent", "user"]

    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Berechnet das Ziel-Datum.

        Args:
            params: {
                "base_date": Optional[str],  # ISO-Format
                "days": Optional[int],
                "weeks": Optional[int],
            }

        Returns:
            {
                "base_date": str,
                "calculated_date": str,
                "days_added": int,
            }
        """
        # Basis-Datum parsen oder heute nehmen
        base_date_str = params.get("base_date")
        if base_date_str:
            base = date.fromisoformat(base_date_str)
        else:
            base = date.today()

        # Tage + Wochen aufaddieren
        days = params.get("days", 0)
        weeks = params.get("weeks", 0)
        total_days = days + (weeks * 7)

        calculated = base + timedelta(days=total_days)

        return {
            "base_date": base.isoformat(),
            "calculated_date": calculated.isoformat(),
            "days_added": total_days,
        }
