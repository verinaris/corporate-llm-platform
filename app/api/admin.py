"""
Admin-API für Audit-Log + DSGVO-Funktionen.

**Zugriff:**
- Admin: voller Zugriff (Audit-Log lesen, User löschen)
- Compliance-Officer: nur Audit-Log lesen
- Andere: kein Zugriff

**DSGVO Art. 17 (Recht auf Vergessenwerden):**
- User-PII wird gelöscht (E-Mail, Passwort-Hash)
- Audit-Log-Einträge bleiben mit pseudonymisierter User-ID
- Token-Logs werden user_id auf "deleted_<user_id>" gesetzt
- Dokumente, Pläne werden gelöscht
- Audit-Log-Eintrag "USER_FULL_DELETE" dokumentiert den Vorgang
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session, col, delete, select

from app.auth.dependencies import get_current_user
from app.auth.permissions import can_read_audit
from app.database import get_session
from app.models import (
    AuditAction,
    AuditLog,
    Document,
    DocumentCollection,
    TokenUsage,
    User,
)
from app.services import audit
from app.services.businessplan import BusinessPlan

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================ #
# Zugriffs-Guard
# ============================================================ #

def _require_admin_or_compliance(user: User) -> None:
    """Wirft 403, wenn nicht Admin oder Compliance-Officer."""
    if not can_read_audit(user.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Nur Admin oder Compliance-Officer haben Zugriff.",
        )


def _require_admin(user: User) -> None:
    """Wirft 403, wenn nicht Admin."""
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Nur Admin hat Zugriff.",
        )


# ============================================================ #
# Audit-Log-Read-API
# ============================================================ #

class AuditEntry(BaseModel):
    """API-Format eines Audit-Log-Eintrags."""

    id: int
    timestamp: datetime
    user_email: str
    user_role: str
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    success: bool


@router.get("/audit-log", response_model=list[AuditEntry])
def list_audit_log(
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[AuditEntry]:
    """
    Audit-Log filtern und durchsuchen.

    Query-Parameter:
    - user_email: Nur Einträge eines bestimmten Users
    - action: Nur eine bestimmte Aktion (z.B. "login_failed")
    - since/until: Zeitraum (ISO datetime)
    - limit: max. Anzahl Ergebnisse (default 100, max 1000)
    """
    _require_admin_or_compliance(user)
    limit = max(1, min(limit, 1000))

    query = select(AuditLog).order_by(col(AuditLog.timestamp).desc())
    if user_email:
        query = query.where(AuditLog.user_email == user_email)
    if action:
        try:
            query = query.where(AuditLog.action == AuditAction(action))
        except ValueError:
            raise HTTPException(400, detail=f"Unbekannte Aktion: {action}")
    if since:
        query = query.where(AuditLog.timestamp >= since)
    if until:
        query = query.where(AuditLog.timestamp <= until)

    rows = session.exec(query.limit(limit)).all()
    return [
        AuditEntry(
            id=r.id or 0,
            timestamp=r.timestamp,
            user_email=r.user_email,
            user_role=r.user_role,
            action=r.action.value if hasattr(r.action, "value") else str(r.action),
            target_type=r.target_type,
            target_id=r.target_id,
            details=r.details,
            ip_address=r.ip_address,
            success=r.success,
        )
        for r in rows
    ]


@router.get("/audit-log/actions")
def list_audit_actions(
    user: User = Depends(get_current_user),
) -> list[str]:
    """Liste aller verfügbaren Audit-Actions (für UI-Filter-Dropdown)."""
    _require_admin_or_compliance(user)
    return [a.value for a in AuditAction]


# ============================================================ #
# DSGVO Art. 17 — Vollständige User-Löschung
# ============================================================ #

class UserDeletionReport(BaseModel):
    """Bericht über das, was bei der DSGVO-Löschung passiert ist."""

    user_email_pseudonym: str
    deleted_documents: int
    deleted_business_plans: int
    pseudonymized_token_logs: int
    pseudonymized_audit_entries: int
    timestamp: datetime


@router.delete("/users/{user_id}/dsgvo-delete", response_model=UserDeletionReport)
def dsgvo_full_delete(
    user_id: int,
    request: Request,
    admin: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserDeletionReport:
    """
    DSGVO Art. 17 — Recht auf Vergessenwerden.

    **Was passiert:**
    1. User-Datensatz: E-Mail + Hash gelöscht (Pseudonym bleibt für Foreign-Keys)
    2. Documents des Users: vollständig gelöscht
    3. BusinessPlans des Users: vollständig gelöscht
    4. TokenUsage-Einträge: user_id auf "deleted_<id>" gesetzt
    5. AuditLog-Einträge: user_email auf "deleted_user_<id>" gesetzt
    6. Neuer Audit-Eintrag "USER_FULL_DELETE" dokumentiert die Löschung

    **Aufbewahrungspflichten beachten:** Audit-Log + Token-Logs bleiben
    pseudonymisiert für gesetzliche Aufbewahrungszeiten (10 Jahre Pharma/Steuer).
    """
    _require_admin(admin)

    target = session.get(User, user_id)
    if not target:
        raise HTTPException(404, detail=f"User {user_id} nicht gefunden")
    if target.id == admin.id:
        raise HTTPException(400, detail="Admin kann sich nicht selbst löschen.")

    pseudonym = f"deleted_user_{user_id}"
    original_email = target.email

    # 1. Dokumente löschen
    docs = session.exec(
        select(Document).where(Document.uploaded_by == original_email)
    ).all()
    deleted_docs = len(docs)
    for d in docs:
        session.delete(d)

    # 2. Businessplans löschen
    plans = session.exec(
        select(BusinessPlan).where(BusinessPlan.user_email == original_email)
    ).all()
    deleted_plans = len(plans)
    for p in plans:
        session.delete(p)

    # 3. TokenUsage pseudonymisieren
    tokens = session.exec(
        select(TokenUsage).where(TokenUsage.user_id == original_email)
    ).all()
    for t in tokens:
        t.user_id = pseudonym
        session.add(t)
    pseudo_tokens = len(tokens)

    # 4. AuditLog pseudonymisieren
    audits = session.exec(
        select(AuditLog).where(AuditLog.user_email == original_email)
    ).all()
    for a in audits:
        a.user_email = pseudonym
        session.add(a)
    pseudo_audits = len(audits)

    # 5. User-PII löschen (Datensatz bleibt mit Pseudonym)
    target.email = pseudonym
    target.password_hash = "DELETED"
    target.is_active = False
    session.add(target)

    session.commit()

    # 6. Audit-Eintrag dokumentiert die Löschung
    audit.log(
        user_email=admin.email,
        user_role=admin.role.value if hasattr(admin.role, "value") else str(admin.role),
        action=AuditAction.USER_FULL_DELETE,
        target_type="user", target_id=str(user_id),
        details={
            "original_email_pseudonym": pseudonym,
            "deleted_documents": deleted_docs,
            "deleted_business_plans": deleted_plans,
            "pseudonymized_token_logs": pseudo_tokens,
            "pseudonymized_audit_entries": pseudo_audits,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return UserDeletionReport(
        user_email_pseudonym=pseudonym,
        deleted_documents=deleted_docs,
        deleted_business_plans=deleted_plans,
        pseudonymized_token_logs=pseudo_tokens,
        pseudonymized_audit_entries=pseudo_audits,
        timestamp=datetime.now(timezone.utc),
    )


# ============================================================ #
# DSGVO Art. 15 — Auskunft (Datenexport)
# ============================================================ #

@router.get("/users/{user_id}/dsgvo-export")
def dsgvo_data_export(
    user_id: int,
    admin: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    """
    DSGVO Art. 15 — Auskunftsrecht.

    Exportiert alle Daten, die wir über den User gespeichert haben.
    """
    _require_admin(admin)

    target = session.get(User, user_id)
    if not target:
        raise HTTPException(404, detail=f"User {user_id} nicht gefunden")

    docs = session.exec(
        select(Document).where(Document.uploaded_by == target.email)
    ).all()
    plans = session.exec(
        select(BusinessPlan).where(BusinessPlan.user_email == target.email)
    ).all()
    tokens = session.exec(
        select(TokenUsage).where(TokenUsage.user_id == target.email)
    ).all()
    audits = session.exec(
        select(AuditLog).where(AuditLog.user_email == target.email)
    ).all()

    audit.log(
        user_email=admin.email,
        user_role=admin.role.value if hasattr(admin.role, "value") else str(admin.role),
        action=AuditAction.USER_DATA_EXPORT,
        target_type="user", target_id=str(user_id),
        details={
            "documents": len(docs),
            "business_plans": len(plans),
            "token_log_entries": len(tokens),
            "audit_entries": len(audits),
        },
    )

    return {
        "user": {
            "id": target.id,
            "email": target.email,
            "role": str(target.role),
            "branch": str(target.branch),
            "is_active": target.is_active,
            "created_at": target.created_at.isoformat() if target.created_at else None,
        },
        "documents": [
            {"id": d.id, "filename": d.filename, "collection": d.collection}
            for d in docs
        ],
        "business_plans": [
            {"id": p.id, "name": p.name, "template_id": p.template_id,
             "created_at": p.created_at.isoformat() if p.created_at else None}
            for p in plans
        ],
        "token_usage_summary": {
            "count": len(tokens),
            "total_tokens": sum(t.total_tokens for t in tokens),
            "total_cost_usd": sum(t.cost_usd for t in tokens),
        },
        "audit_entries_count": len(audits),
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
    }
