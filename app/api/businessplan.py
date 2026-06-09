"""
REST-API für den Businessplan-Generator (Phase 5+).

Endpoints:
- GET    /businessplan/templates           Verfügbare Vorlagen
- GET    /businessplan/templates/{id}/default   Default-Werte einer Vorlage
- POST   /businessplan/generate            Plan berechnen (ohne speichern)
- POST   /businessplan/                    Plan speichern (DB)
- GET    /businessplan/                    Eigene Pläne auflisten
- GET    /businessplan/{id}                Einzelnen Plan laden
- DELETE /businessplan/{id}                Plan löschen
- POST   /businessplan/{id}/export/docx    Word-Export
- POST   /businessplan/{id}/export/xlsx    Excel-Export
- POST   /businessplan/{id}/export/pdf     PDF-Export
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.branches.profiles import (
    get_businessplan_templates_for_branch,
    get_industry_for_businessplan,
)
from app.database import get_session
from app.models import AuditAction, User
from app.services import audit
from app.services.businessplan import (
    BusinessPlan,
    BusinessPlanInput,
    BusinessPlanResult,
    BusinessPlanSummary,
    TemplateInfo,
    generate_business_plan,
    get_template_default,
    list_templates,
)
from app.services.businessplan.export import export_docx, export_pdf, export_xlsx

router = APIRouter(prefix="/businessplan", tags=["businessplan"])


# ============================================================ #
# Templates
# ============================================================ #

@router.get("/templates", response_model=list[TemplateInfo])
def get_templates(user: User = Depends(get_current_user)) -> list[TemplateInfo]:
    """
    Liefert verfügbare Businessplan-Vorlagen für den eingeloggten User.

    **Filter-Logik:**
    - Admin sieht alle Vorlagen (zum Testen / Demo)
    - Andere User sehen nur Vorlagen, die zu ihrem Branchen-Profil passen
    """
    all_templates = list_templates()

    if user.role.value == "admin" if hasattr(user.role, "value") else user.role == "admin":
        return all_templates

    allowed_ids = get_businessplan_templates_for_branch(user.branch)
    return [t for t in all_templates if t.id in allowed_ids]


@router.get("/templates/{template_id}/default", response_model=BusinessPlanInput)
def get_template_default_input(
    template_id: str,
    user: User = Depends(get_current_user),
) -> BusinessPlanInput:
    """
    Default-Werte zu einer Vorlage (zum Vorbefüllen des UI-Formulars).

    Setzt automatisch die richtige `industry` basierend auf der User-Branche,
    falls die Vorlage keine eigene definiert hat.
    """
    defaults = get_template_default(template_id)
    # Industry vom User-Profil übernehmen, wenn die Vorlage "generic" ist
    if defaults.industry == "generic":
        defaults.industry = get_industry_for_businessplan(user.branch)
    return defaults


# ============================================================ #
# Generate (ohne speichern) — preview
# ============================================================ #

@router.post("/generate", response_model=BusinessPlanResult)
async def generate(
    payload: BusinessPlanInput,
    llm_model: str | None = None,
    user: User = Depends(get_current_user),
) -> BusinessPlanResult:
    """
    Berechnet einen Plan, ohne ihn zu speichern (für Live-Vorschau im UI).

    `llm_model` Optional (Query-Parameter): 'claude-sonnet-4-6', 'qwen2.5:7b', ...
    oder None für regelbasierten Fallback-Summary.
    """
    return await generate_business_plan(payload, llm_model=llm_model)


# ============================================================ #
# CRUD — gespeicherte Pläne
# ============================================================ #

@router.post("", response_model=int, status_code=status.HTTP_201_CREATED)
def save_plan(
    payload: BusinessPlanInput,
    last_score: int = 0,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> int:
    """Speichert einen Plan in der DB. Liefert die neue ID."""
    plan = BusinessPlan(
        user_email=user.email,
        name=payload.startup_name,
        template_id=payload.template_id,
        input_json=payload.model_dump_json(),
        last_score=last_score,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)

    audit.log(
        user_email=user.email,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.PLAN_CREATED,
        target_type="business_plan", target_id=str(plan.id),
        details={"template_id": plan.template_id, "score": last_score},
    )
    return int(plan.id)


@router.get("", response_model=list[BusinessPlanSummary])
def list_plans(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[BusinessPlanSummary]:
    """Liefert alle Pläne des aktuellen Users (Admin sieht alle)."""
    query = select(BusinessPlan)
    if user.role != "admin":
        query = query.where(BusinessPlan.user_email == user.email)
    query = query.order_by(BusinessPlan.updated_at.desc())
    rows = session.exec(query).all()
    return [
        BusinessPlanSummary(
            id=r.id or 0,
            name=r.name,
            template_id=r.template_id,
            last_score=r.last_score,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/{plan_id}", response_model=BusinessPlanInput)
def get_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BusinessPlanInput:
    """Lädt einen einzelnen Plan (nur Input-Daten)."""
    plan = _load_plan(plan_id, user, session)
    return BusinessPlanInput.model_validate(json.loads(plan.input_json))


@router.put("/{plan_id}", response_model=int)
def update_plan(
    plan_id: int,
    payload: BusinessPlanInput,
    last_score: int = 0,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> int:
    """Aktualisiert einen bestehenden Plan."""
    plan = _load_plan(plan_id, user, session)
    plan.name = payload.startup_name
    plan.template_id = payload.template_id
    plan.input_json = payload.model_dump_json()
    plan.last_score = last_score
    plan.updated_at = datetime.now(timezone.utc)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return int(plan.id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    """Löscht einen Plan."""
    plan = _load_plan(plan_id, user, session)
    plan_name = plan.name
    session.delete(plan)
    session.commit()
    audit.log(
        user_email=user.email,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.PLAN_DELETED,
        target_type="business_plan", target_id=str(plan_id),
        details={"name": plan_name},
    )


# ============================================================ #
# Export — Word, Excel, PDF
# ============================================================ #

@router.post("/export/{fmt}")
async def export_plan(
    fmt: str,
    payload: BusinessPlanInput,
    llm_model: str | None = None,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Generiert Plan und liefert direkt als Download.

    `fmt` muss 'docx', 'xlsx' oder 'pdf' sein.
    """
    if fmt not in ("docx", "xlsx", "pdf"):
        raise HTTPException(400, detail=f"Unbekanntes Format: {fmt}")

    result = await generate_business_plan(payload, llm_model=llm_model)

    safe = _safe_name(payload.startup_name) or "businessplan"

    if fmt == "docx":
        data = export_docx(result)
        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        filename = f"{safe}_businessplan.docx"
    elif fmt == "xlsx":
        data = export_xlsx(result)
        media = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"{safe}_finanzmodell.xlsx"
    else:  # pdf
        data = export_pdf(result)
        media = "application/pdf"
        filename = f"{safe}_executive_summary.pdf"

    from io import BytesIO
    return StreamingResponse(
        BytesIO(data),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================ #
# Helpers
# ============================================================ #

def _load_plan(plan_id: int, user: User, session: Session) -> BusinessPlan:
    """Lädt einen Plan + prüft Ownership."""
    plan = session.get(BusinessPlan, plan_id)
    if not plan:
        raise HTTPException(404, detail="Plan nicht gefunden")
    if user.role != "admin" and plan.user_email != user.email:
        raise HTTPException(403, detail="Kein Zugriff auf diesen Plan")
    return plan


def _safe_name(name: str) -> str:
    return "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in (name or "").lower()
    )[:50]
