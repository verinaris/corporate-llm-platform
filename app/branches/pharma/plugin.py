"""
Pharma-Außendienst-Branche — Phase 2c: lebendig!

Aktiv:
- get_system_prompt() → HWG/AMG-konformer Branchen-Prompt
- post_process_response() → Pflicht-Disclaimer wird automatisch angehängt
- required_disclaimer → Disclaimer-Text auch separat abrufbar

Geplant für Phase 3:
- pre_process_messages() → PII-Detektor (Patientendaten blockieren)
"""

from app.branches.base import BranchPlugin
from app.branches.pharma.prompts import PHARMA_DISCLAIMER, PHARMA_SYSTEM_PROMPT
from app.schemas import ChatMessage


class PharmaPlugin(BranchPlugin):
    """Pharma-Außendienst — voll aktiviert (Phase 2c)."""

    branch_code = "pharma"
    display_name = "Pharma-Außendienst"

    # ------------------------------------------------------------------ #
    # System-Prompt
    # ------------------------------------------------------------------ #
    def get_system_prompt(self) -> str | None:
        return PHARMA_SYSTEM_PROMPT

    # ------------------------------------------------------------------ #
    # Pre-Processing — Phase 3 (PII-Filter)
    # ------------------------------------------------------------------ #
    def pre_process_messages(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        # TODO Phase 3: PII-Detektor (z.B. Microsoft Presidio)
        #   → bei Treffer: raise ValueError("Patientendaten blockiert")
        return messages

    # ------------------------------------------------------------------ #
    # Post-Processing
    # ------------------------------------------------------------------ #
    def post_process_response(self, response_text: str) -> str:
        """Hängt den Pflicht-Disclaimer an jede Antwort an."""
        if PHARMA_DISCLAIMER.strip() in response_text:
            # Falls bereits drin (z.B. nach Mehrfach-Aufruf): nicht doppeln
            return response_text
        return response_text + PHARMA_DISCLAIMER

    # ------------------------------------------------------------------ #
    # Disclaimer
    # ------------------------------------------------------------------ #
    @property
    def required_disclaimer(self) -> str | None:
        return PHARMA_DISCLAIMER
