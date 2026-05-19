"""
Branchen-Plugin-Interface.

Definiert die "Steckdose", in die jedes Branchen-Plugin passen muss.
Jede Branche kann an 3 Stellen eingreifen:

1. get_system_prompt()        → fügt einen Branchen-System-Prompt hinzu
2. pre_process_messages()      → vor dem LLM-Call (z.B. PII-Filter)
3. post_process_response()     → nach dem LLM-Call (z.B. Disclaimer)

Analogie: Eine Branche ist wie eine Brille, die ein User aufsetzt —
sie färbt Input und Output, ohne den Rest des Systems zu verändern.
"""

from abc import ABC, abstractmethod

from app.schemas import ChatMessage


class BranchPlugin(ABC):
    """Basis für branchenspezifische Anpassungen."""

    #: Maschinen-Code der Branche ("pharma", "legal", ...) — eindeutig
    branch_code: str = "base"

    #: Anzeigename der Branche (für UI)
    display_name: str = "Base"

    # ------------------------------------------------------------------ #
    # 1) System-Prompt
    # ------------------------------------------------------------------ #
    @abstractmethod
    def get_system_prompt(self) -> str | None:
        """
        Liefert einen Branchen-System-Prompt oder None.

        Wird beim Chat-Request automatisch vorangestellt, wenn vorhanden.
        Wenn die Konversation bereits einen User-System-Prompt hat,
        wird der Branchen-Prompt KONKATENIERT (Branche zuerst).
        """
        ...

    # ------------------------------------------------------------------ #
    # 2) Pre-Processing (vor LLM-Call)
    # ------------------------------------------------------------------ #
    def pre_process_messages(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        """
        Wird VOR dem LLM-Call auf die Messages angewendet.

        Default: keine Änderung.
        Branchen können hier z.B. PII-Filter, Verbots-Check, Längen-Check
        einbauen. Bei Verstoß: ValueError werfen (führt zu HTTP 400).
        """
        return messages

    # ------------------------------------------------------------------ #
    # 3) Post-Processing (nach LLM-Call)
    # ------------------------------------------------------------------ #
    def post_process_response(self, response_text: str) -> str:
        """
        Wird NACH dem LLM-Call auf den Antworttext angewendet.

        Default: keine Änderung.
        Branchen können hier z.B. Disclaimer anhängen, Begriffe filtern,
        Quellenangabe erzwingen.
        """
        return response_text

    # ------------------------------------------------------------------ #
    # Hilfs-Properties
    # ------------------------------------------------------------------ #
    @property
    def required_disclaimer(self) -> str | None:
        """Pflicht-Disclaimer, der von post_process angehängt werden kann."""
        return None
