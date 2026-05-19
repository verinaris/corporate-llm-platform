"""
Pharma-Außendienst-Branche.

⚠️  GERÜST — INHALT WIRD IN PHASE 2 + 3 GEFÜLLT.

Geplante Implementierung:

Phase 2:
- get_system_prompt() → HWG-/AMG-konformer System-Prompt:
  "Du unterstützt Pharma-Referenten. Keine vergleichende Werbung.
   Keine Superlative. Bei Therapieaussagen: Quellen pflicht. ..."
- required_disclaimer → fester Disclaimer-Text
- post_process_response → hängt Disclaimer automatisch an

Phase 3:
- pre_process_messages → PII-Detektor (blockt Namen, GebDatum, Versich.Nr.)
- post_process_response → Quellenangabe-Check, HWG-Aussagen-Filter
- Anbindung an Fachinfo-RAG-Sammlung
"""

from app.branches.base import BranchPlugin
from app.schemas import ChatMessage


class PharmaPlugin(BranchPlugin):
    """Pharma-Außendienst — leeres Gerüst (Phase 2 + 3)."""

    branch_code = "pharma"
    display_name = "Pharma-Außendienst"

    # ------------------------------------------------------------------ #
    # System-Prompt
    # ------------------------------------------------------------------ #
    def get_system_prompt(self) -> str | None:
        # TODO Phase 2: HWG-/AMG-konformer System-Prompt einsetzen
        return None

    # ------------------------------------------------------------------ #
    # Pre-Processing
    # ------------------------------------------------------------------ #
    def pre_process_messages(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        # TODO Phase 3: PII-Detektor (z.B. mit presidio-analyzer)
        #               → bei Treffer: raise ValueError("Patientendaten blockiert")
        return super().pre_process_messages(messages)

    # ------------------------------------------------------------------ #
    # Post-Processing
    # ------------------------------------------------------------------ #
    def post_process_response(self, response_text: str) -> str:
        # TODO Phase 2: Disclaimer anhängen
        # TODO Phase 3: HWG-Superlativ-Filter, Quellen-Pflicht-Check
        return super().post_process_response(response_text)

    # ------------------------------------------------------------------ #
    # Disclaimer
    # ------------------------------------------------------------------ #
    @property
    def required_disclaimer(self) -> str | None:
        # TODO Phase 2: Konkreter HWG-/AMG-Disclaimer-Text
        return None
