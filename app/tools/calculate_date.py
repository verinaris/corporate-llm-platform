"""
CalculateDateTool — Berechnet Datumsangaben für Fristen und Termine.

Zwei Modi:

Mode 1 (Forward-Add):  base_date + days/weeks = neues Datum
  Beispiel: "Welches Datum ist in 30 Tagen?" oder "in 6 Wochen ab 15.06."

Mode 2 (Difference):   base_date → target_date = Anzahl Tage dazwischen
  Beispiel: "In wie vielen Tagen ist Weihnachten?"

Wird vom LLM aufgerufen, wenn Fristen oder Termine berechnet werden müssen.
"""

from datetime import date, timedelta
from typing import Any

from app.tools.base import BaseTool


class CalculateDateTool(BaseTool):
    """Berechnet Datumsangaben (Fristen, Termine, Differenzen)."""

    name = "calculate_date"
    description = (
        "Berechnet Datumsangaben in zwei Modi: "
        "(1) Forward-Add — Basis-Datum + Tage/Wochen = neues Datum; "
        "(2) Difference — Anzahl Tage zwischen zwei Daten. "
        "Wenn target_date gesetzt ist, wird Mode 2 verwendet, sonst Mode 1. "
        "Nützlich für Fristen, Termine und Zeitabstände."
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
                "description": (
                    "MODE 1 (Forward-Add): Tage hinzufügen "
                    "(negativ = in Vergangenheit)."
                ),
            },
            "weeks": {
                "type": "integer",
                "description": (
                    "MODE 1 (Forward-Add): Wochen hinzufügen "
                    "(wird intern zu Tagen)."
                ),
            },
            "target_date": {
                "type": "string",
                "format": "date",
                "description": (
                    "MODE 2 (Difference): Ziel-Datum im ISO-Format (YYYY-MM-DD). "
                    "Wenn gesetzt, berechnet das Tool die Anzahl Tage zwischen "
                    "base_date und target_date."
                ),
            },
        },
        "required": [],
    }

    # Konfiguration
    requires_human_oversight = False  # Mathematik ist harmlos
    allowed_roles = ["admin", "compliance-officer", "pharma-referent", "user"]

    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Berechnet je nach Modus.

        Returns Mode 1 (Forward-Add):
            {
                "mode": "forward_add",
                "base_date": str,           # ISO
                "calculated_date": str,      # ISO
                "days_added": int,
            }

        Returns Mode 2 (Difference):
            {
                "mode": "difference",
                "base_date": str,            # ISO (typisch: heute)
                "target_date": str,          # ISO
                "days_difference": int,      # Anzahl Tage (positiv = Ziel in Zukunft)
                "weeks_difference": float,   # Anzahl Wochen (gerundet auf 1 Dezimal)
                "is_past": bool,             # True wenn Ziel in Vergangenheit
            }
        """
        # Basis-Datum parsen oder heute nehmen
        base_date_str = params.get("base_date")
        if base_date_str:
            base = date.fromisoformat(base_date_str)
        else:
            base = date.today()

        # MODE-Selection: Wenn target_date gesetzt → Diff-Mode
        target_date_str = params.get("target_date")
        if target_date_str:
            return self._mode_difference(base, target_date_str)

        # Sonst: Forward-Add-Mode
        return self._mode_forward_add(base, params)

    def _mode_forward_add(self, base: date, params: dict) -> dict[str, Any]:
        """Mode 1: Basis-Datum + Tage/Wochen = neues Datum."""
        days = params.get("days", 0)
        weeks = params.get("weeks", 0)
        total_days = days + (weeks * 7)

        calculated = base + timedelta(days=total_days)

        return {
            "mode": "forward_add",
            "base_date": base.isoformat(),
            "calculated_date": calculated.isoformat(),
            "days_added": total_days,
        }

    def _mode_difference(self, base: date, target_date_str: str) -> dict[str, Any]:
        """Mode 2: Anzahl Tage zwischen base_date und target_date."""
        target = date.fromisoformat(target_date_str)
        delta = target - base
        days_diff = delta.days

        return {
            "mode": "difference",
            "base_date": base.isoformat(),
            "target_date": target.isoformat(),
            "days_difference": days_diff,
            "weeks_difference": round(days_diff / 7, 1),
            "is_past": days_diff < 0,
        }
