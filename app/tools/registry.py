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

import inspect
from typing import Any

from app.models import AuditAction
from app.services.approval import consume_token
from app.services.approval_request import create_request as create_pending_request
from app.services.audit import log as audit_log
from app.tools.base import BaseTool


class ToolNotFoundError(Exception):
    """Wird geworfen, wenn ein nicht-registriertes Tool aufgerufen wird."""
    pass


class ApprovalPendingError(Exception):
    """
    Wird geworfen, wenn ein sensitives Tool ohne Token aufgerufen wurde
    und automatisch ein PendingApproval angelegt wurde.

    Analogie: 'Antrag ist im Postkasten, Chef entscheidet noch.'
    """
    def __init__(self, request_id: int, tool_name: str):
        self.request_id = request_id
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' benoetigt Compliance-Freigabe. "
            f"Antrag #{request_id} wurde eingereicht."
        )


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
    def _authorize(
        cls,
        name: str,
        params: dict,
        user_role: str,
        user_email: str,
        approval_token: str | None,
    ) -> BaseTool:
        """
        Rollen- und Freigabepruefung, gemeinsam fuer execute() und execute_async().

        Ohne Token legt ein freigabepflichtiges Tool einen Antrag an und wirft
        ApprovalPendingError. Mit Token wird dieser geprueft und verbraucht.
        """
        tool = cls._tools.get(name)
        if not tool:
            # Kein Audit hier -- Tool existiert gar nicht
            raise ToolNotFoundError(f"Tool '{name}' not found")

        if user_role not in tool.allowed_roles:
            audit_log(
                user_email=user_email,
                action=AuditAction.TOOL_DENIED,
                user_role=user_role,
                target_type="tool",
                target_id=name,
                details={"reason": "role_not_allowed", "required_roles": list(tool.allowed_roles)},
                success=False,
            )
            raise PermissionDeniedError(f"Role '{user_role}' is not allowed to use tool '{name}'")

        if tool.requires_human_oversight:
            if approval_token:
                if not consume_token(approval_token, name, params):
                    audit_log(
                        user_email=user_email,
                        action=AuditAction.TOOL_DENIED,
                        user_role=user_role,
                        target_type="tool",
                        target_id=name,
                        details={"reason": "approval_token_invalid"},
                        success=False,
                    )
                    raise PermissionDeniedError(f"Approval-Token für '{name}' ist ungültig oder abgelaufen")
            else:
                pending = create_pending_request(
                    requester_email=user_email,
                    requester_role=user_role,
                    tool_name=name,
                    params=params,
                    reason=None,
                )
                audit_log(
                    user_email=user_email,
                    action=AuditAction.TOOL_DENIED,
                    user_role=user_role,
                    target_type="tool",
                    target_id=name,
                    details={"reason": "approval_pending", "pending_request_id": pending.id},
                    success=False,
                )
                raise ApprovalPendingError(request_id=pending.id, tool_name=name)
        return tool

    @classmethod
    def _audit_result(cls, name, params, user_role, user_email, result=None, error=None) -> None:
        if error is not None:
            audit_log(
                user_email=user_email,
                action=AuditAction.TOOL_FAILED,
                user_role=user_role,
                target_type="tool",
                target_id=name,
                details={
                    "error_type": error.__class__.__name__,
                    "error_message": str(error),
                    "params_keys": list(params.keys()),
                },
                success=False,
            )
        else:
            audit_log(
                user_email=user_email,
                action=AuditAction.TOOL_EXECUTED,
                user_role=user_role,
                target_type="tool",
                target_id=name,
                details={"params_keys": list(params.keys()), "result_type": type(result).__name__},
                success=True,
            )

    @classmethod
    def execute(
        cls,
        name: str,
        params: dict,
        user_id: int | None = None,
        user_role: str = "admin",
        user_email: str = "system@verinaris.local",
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Fuehrt ein (synchrones) Tool aus, mit Berechtigungspruefung und Audit-Log.

        Asynchrone Tools (z.B. RegulationImportTool) muessen ueber
        execute_async() laufen; hier wuerde ihr Ergebnis sonst als nie
        ausgefuehrte Coroutine verloren gehen.
        """
        tool = cls._authorize(name, params, user_role, user_email, approval_token)
        try:
            result = tool.execute(params, user_id=user_id)
            if inspect.isawaitable(result):
                if hasattr(result, "close"):
                    result.close()
                raise TypeError(f"Tool '{name}' ist asynchron und muss über execute_async() laufen.")
        except Exception as e:
            cls._audit_result(name, params, user_role, user_email, error=e)
            raise
        cls._audit_result(name, params, user_role, user_email, result=result)
        return result

    @classmethod
    async def execute_async(
        cls,
        name: str,
        params: dict,
        user_id: int | None = None,
        user_role: str = "admin",
        user_email: str = "system@verinaris.local",
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        """Wie execute(), wartet aber auf asynchrone Tools."""
        tool = cls._authorize(name, params, user_role, user_email, approval_token)
        try:
            result = tool.execute(params, user_id=user_id)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            cls._audit_result(name, params, user_role, user_email, error=e)
            raise
        cls._audit_result(name, params, user_role, user_email, result=result)
        return result

    @classmethod
    def clear(cls) -> None:
        """Entfernt alle registrierten Tools (für Tests)."""
        cls._tools.clear()
