"""
Vier-Augen-Freigaben ueber die API (Block "Freigaben Ende-zu-Ende", F1).

Vorher griff die Oberflaeche direkt auf die Services zu, am Backend vorbei:
ohne serverseitige Rechtepruefung und ohne Audit der Entscheidung.

Endpoints:
- GET  /approvals                 offene Antraege (alle Angemeldeten)
- POST /approvals/{id}/approve    freigeben (can_approve, nicht der eigene Antrag)
- POST /approvals/{id}/reject     ablehnen, Begruendung Pflicht

Sichtbarkeit: Werkzeug, Antragsteller, Status und Alter sieht jeder (Transparenz).
Die Parameter (z.B. URL und Ziel-Sammlung) nur, wer entscheiden darf, und der
Antragsteller selbst -- sonst verraet die Liste Namen fremder Sammlungen.

Analogie: der Posteingang am Schwarzen Brett. Jeder sieht, dass Post da ist;
den Inhalt liest nur, wer zustaendig ist, und stempeln darf nie, wer den Brief
selbst geschrieben hat.
"""

import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.permissions import can_approve
from app.models import ApprovalStatus, AuditAction, User
from app.services import audit
from app.services.approval_request import (
    approve_request,
    get_request,
    list_pending,
    reject_request,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalOut(BaseModel):
    id: int
    tool_name: str
    requester_email: str
    requester_role: str
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    params: Optional[dict[str, Any]] = None   # nur fuer Berechtigte
    decided_by_email: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_notes: Optional[str] = None


class ApprovalListOut(BaseModel):
    can_decide: bool
    items: list[ApprovalOut]


class DecisionIn(BaseModel):
    notes: Optional[str] = None


def _rv(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _same(a: str, b: str) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _out(req, user: User) -> ApprovalOut:
    show = can_approve(user.role) or _same(req.requester_email, user.email)
    params = None
    if show:
        try:
            params = json.loads(req.params_json)
        except Exception:
            params = {"_raw": req.params_json}
    return ApprovalOut(
        id=req.id,
        tool_name=req.tool_name,
        requester_email=req.requester_email,
        requester_role=req.requester_role,
        reason=req.reason,
        status=_rv(req.status),
        created_at=getattr(req, "created_at", None),
        params=params,
        decided_by_email=req.decided_by_email,
        decided_at=getattr(req, "decided_at", None),
        decision_notes=req.decision_notes,
    )


def _audit(request: Request, user: User, action: AuditAction, req_id: int,
           details: dict, success: bool = True) -> None:
    audit.log(
        user_email=user.email,
        action=action,
        user_role=_rv(user.role),
        target_type="approval",
        target_id=str(req_id),
        details=details,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=success,
    )


def _check_decider(request: Request, user: User, req_id: int, decision: str):
    """Laedt den Antrag und prueft Recht + Vier-Augen. Wirft 403/404/409."""
    req = get_request(req_id)
    if req is None:
        raise HTTPException(404, detail="Antrag nicht gefunden")
    if not can_approve(user.role):
        _audit(request, user, AuditAction.APPROVAL_DENIED, req_id,
               {"decision": decision, "reason": "role_not_allowed"}, success=False)
        raise HTTPException(403, detail="Sie dürfen über Freigabe-Anträge nicht entscheiden.")
    if _same(req.requester_email, user.email):
        _audit(request, user, AuditAction.APPROVAL_DENIED, req_id,
               {"decision": decision, "reason": "own_request"}, success=False)
        raise HTTPException(403, detail="Über den eigenen Antrag kann nicht entschieden werden (Vier-Augen-Prinzip).")
    if req.status != ApprovalStatus.PENDING:
        raise HTTPException(409, detail=f"Antrag wurde bereits entschieden ({_rv(req.status)}).")
    return req


@router.get("", response_model=ApprovalListOut)
def list_approvals(user: User = Depends(get_current_user)) -> ApprovalListOut:
    """Offene Antraege, aelteste zuerst."""
    return ApprovalListOut(
        can_decide=can_approve(user.role),
        items=[_out(r, user) for r in list_pending()],
    )


@router.post("/{req_id}/approve", response_model=ApprovalOut)
def approve(
    req_id: int,
    payload: DecisionIn,
    request: Request,
    user: User = Depends(get_current_user),
) -> ApprovalOut:
    req = _check_decider(request, user, req_id, "approve")
    try:
        updated, _token = approve_request(
            request_id=req_id,
            approver_email=user.email,
            approver_role=_rv(user.role),
            decision_notes=(payload.notes or "").strip() or None,
        )
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    _audit(request, user, AuditAction.APPROVAL_GRANTED, req_id, {
        "tool": req.tool_name,
        "requester": req.requester_email,
        "notes": bool(payload.notes and payload.notes.strip()),
    })
    return _out(updated, user)


@router.post("/{req_id}/reject", response_model=ApprovalOut)
def reject(
    req_id: int,
    payload: DecisionIn,
    request: Request,
    user: User = Depends(get_current_user),
) -> ApprovalOut:
    if not payload.notes or not payload.notes.strip():
        raise HTTPException(422, detail="Für eine Ablehnung ist eine Begründung Pflicht.")
    req = _check_decider(request, user, req_id, "reject")
    try:
        updated = reject_request(
            request_id=req_id,
            approver_email=user.email,
            approver_role=_rv(user.role),
            decision_notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    _audit(request, user, AuditAction.APPROVAL_REJECTED, req_id, {
        "tool": req.tool_name,
        "requester": req.requester_email,
    })
    return _out(updated, user)
