"""
BaseTool — Abstrakte Basis-Klasse für alle Verinaris-Tools.

Jedes Tool erbt von BaseTool und implementiert die execute()-Methode.
Die Registry verwaltet alle Tools und sorgt für:
- Rollen-basierte Berechtigungsprüfung
- Audit-Log-Eintrag bei jedem Aufruf
- Human-in-the-Loop-Konfiguration pro Tool
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstrakte Basis-Klasse für alle Tools."""

    # Pflicht-Felder, die jedes Tool definieren muss
    name: str = ""
    description: str = ""
    parameters_schema: dict = {}

    # Optional: Konfiguration
    requires_human_oversight: bool = False
    allowed_roles: list[str] = ["admin"]

    @abstractmethod
    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Führt das Tool aus.

        Args:
            params: Tool-spezifische Parameter (validiert gegen parameters_schema)
            user_id: ID des aufrufenden Users (für Audit-Log)

        Returns:
            dict mit Tool-Ergebnis
        """
        pass

    def to_anthropic_format(self) -> dict:
        """Konvertiert das Tool ins Anthropic Tool-Use-Format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema,
        }

    def to_ollama_format(self) -> dict:
        """Konvertiert das Tool ins Ollama Tool-Use-Format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
