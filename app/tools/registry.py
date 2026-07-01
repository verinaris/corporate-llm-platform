"""
ToolRegistry — Zentrale Verwaltung aller Verinaris-Tools.

Verantwortlichkeiten:
- Tool-Registrierung beim Application-Start
- Rollen-basierte Berechtigungsprüfung
- Audit-Log-Eintrag bei jedem Tool-Aufruf
- Provider-Format-Konvertierung (Anthropic / Ollama)

Verwendung:
    ToolRegistry.register(SearchDocumentsTool())
    ToolRegistry.execute("search_documents", {"query": "..."}, user)
"""

from typing import Any

from app.models import AuditAction
from app.services.audit import log as audit_log
from app.tools.base import BaseTool


class ToolNotFoundError(Exception):
    """Wird geworfen, wenn ein nicht-registriertes Tool aufgerufen wird."""
    pass


class PermissionDeniedError(Exception):
    """Wird geworfen, wenn ein User keine Berechtigung für ein Tool hat."""
    pass


class ToolRegistry:
    """Zentrale Verwaltung aller verfügbaren Tools."""

    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """
        Registriert ein Tool in der Registry.

        Args:
            tool: Instanz einer BaseTool-Subklasse

        Raises:
            ValueError: Wenn Tool-Name leer ist oder schon existiert
        """
        if not tool.name:
            raise ValueError(f"Tool {tool.__class__.__name__} has no name")
        if tool.name in cls._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        """Gibt das Tool mit dem angegebenen Namen zurück (oder None)."""
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> list[BaseTool]:
        """Gibt alle registrierten Tools zurück."""
        return list(cls._tools.values())

    @classmethod
    def get_for_role(cls, role: str) -> list[BaseTool]:
        """
        Gibt alle Tools zurück, die für die angegebene Rolle erlaubt sind.

        Args:
            role: User-Rolle (z.B. "admin", "compliance-officer")

        Returns:
            Liste der erlaubten Tools
        """
        return [
            tool for tool in cls._tools.values()
            if role in tool.allowed_roles
        ]

    @classmethod
    def execute(
        cls,
        name: str,
        params: dict,
        user_id: int | None = None,
        user_role: str = "admin",
        user_email: str = "system@verinaris.local",
    ) -> dict[str, Any]:
        """
        Führt ein Tool aus mit Berechtigungsprüfung und Audit-Log.

        Jeder Aufruf erzeugt einen Audit-Log-Eintrag — auch bei
        fehlgeschlagenen Berechtigungs-Checks oder Tool-Fehlern
        (DSB-Nachvollziehbarkeit).

        Args:
            name: Name des Tools
            params: Tool-Parameter
            user_id: ID des aufrufenden Users (für Debug)
            user_role: Rolle des Users (für Berechtigungsprüfung)
            user_email: Email des Users (für Audit-Log)

        Returns:
            Tool-Ergebnis

        Raises:
            ToolNotFoundError: Tool existiert nicht
            PermissionDeniedError: User hat keine Berechtigung
        """
        tool = cls._tools.get(name)
        if not tool:
            # Kein Audit hier — Tool existiert gar nicht
            raise ToolNotFoundError(f"Tool '{name}' not found")

        # Berechtigungs-Check
        if user_role not in tool.allowed_roles:
            audit_log(
                user_email=user_email,
                action=AuditAction.TOOL_DENIED,
                user_role=user_role,
                target_type="tool",
                target_id=name,
                details={
                    "reason": "role_not_allowed",
                    "required_roles": list(tool.allowed_roles),
                },
                success=False,
            )
            raise PermissionDeniedError(
                f"Role '{user_role}' is not allowed to use tool '{name}'"
            )

        # Tool ausführen (Fehler-tolerant für Audit)
        try:
            result = tool.execute(params, user_id=user_id)
        except Exception as e:
            audit_log(
                user_email=user_email,
                action=AuditAction.TOOL_FAILED,
                user_role=user_role,
                target_type="tool",
                target_id=name,
                details={
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                    "params_keys": list(params.keys()),
                },
                success=False,
            )
            raise

        # Erfolg loggen
        audit_log(
            user_email=user_email,
            action=AuditAction.TOOL_EXECUTED,
            user_role=user_role,
            target_type="tool",
            target_id=name,
            details={
                "params_keys": list(params.keys()),
                "result_type": type(result).__name__,
            },
            success=True,
        )

        return result

    @classmethod
    def clear(cls) -> None:
        """Entfernt alle registrierten Tools (für Tests)."""
        cls._tools.clear()
