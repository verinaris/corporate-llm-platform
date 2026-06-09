"""
Audit-Logging Service (Phase 6a — Compliance).

Zentraler Einstiegspunkt für alle Module: `audit.log(...)`.

**Designprinzipien:**
- **Best-effort**: Audit-Fehler darf NIEMALS die Hauptaktion abbrechen
- **Synchron, aber leichtgewichtig**: SQLite-Insert, kein async-Overhead
- **Strukturiert**: `details` als JSON-String (zukunftssicher für Reporting)
- **DSGVO-bewusst**: keine sensiblen Inhalte loggen (z.B. Chat-Nachrichten);
  nur Metadaten (User, Aktion, Target-ID, optional kleiner Kontext)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.database import engine
from app.models import AuditAction, AuditLog

_log = logging.getLogger(__name__)


def log(
    user_email: str,
    action: AuditAction,
    *,
    user_role: str = "unknown",
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    session: Optional[Session] = None,
) -> None:
    """
    Loggt eine compliance-relevante Aktion.

    **Best-effort**: schlägt das Logging fehl, wird das geloggt aber
    NICHT geworfen — die Haupt-Aktion soll NIE durch Audit-Fehler
    blockiert werden.

    Args:
        user_email: Wer die Aktion ausgeführt hat (auch pseudonymisiert OK)
        action: Aus AuditAction-Enum
        user_role: Rolle zum Zeitpunkt (für historische Korrektheit)
        target_type: Optional, z.B. "document", "plan", "user"
        target_id: Optional, ID des betroffenen Objekts
        details: Optional, dict — wird zu JSON serialisiert
        ip_address: Optional, Quell-IP
        user_agent: Optional, Browser-/Client-ID
        success: True bei erfolgreicher Aktion
        session: Optional, eigene DB-Session (sonst neue)
    """
    try:
        entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_email=user_email or "anonymous",
            user_role=user_role,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        if session is not None:
            session.add(entry)
            session.commit()
        else:
            with Session(engine) as s:
                s.add(entry)
                s.commit()
    except Exception as exc:
        # NIEMALS werfen — Audit darf Hauptaktion nicht abbrechen
        _log.error(
            "Audit-Log fehlgeschlagen für %s/%s: %s",
            user_email, action.value, exc,
        )
