"""
Generic-Branche.

Default-Plugin ohne speziellen Eingriff. Wird verwendet, wenn ein User
keiner spezifischen Branche zugeordnet ist.
"""

from app.branches.base import BranchPlugin


class GenericPlugin(BranchPlugin):
    """Verhält sich neutral — kein System-Prompt, keine Filter."""

    branch_code = "generic"
    display_name = "Allgemein"

    def get_system_prompt(self) -> str | None:
        return None
