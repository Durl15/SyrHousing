"""
Grants V2 API — eligibility-matched grant discovery with PDF/CSV export.

Prefix : /api/v2/grants
Tags   : grants-v2
"""
import json
import logging
import traceback
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.grants_db import Grant, EligibilityCriteria, GrantApplication
from ..services.eligibility_engine import (
    match_grants,
    VALID_PROPERTY_TYPES,
    VALID_REPAIR_CATEGORIES,
)
from ..services.grants_export import export_grants_csv, export_grants_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/grants", tags=["grants-v2"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class EligibilityCriteriaSchema(BaseModel):
    requires_owner_occupied: bool = True
    requires_primary_residence: bool = True
    requires_us_citizen: bool = False
    geographic_restriction: Optional[str] = None
    credit_score_min: Optional[int] = None
    first_time_buyer_required: bool = False
    additional_notes: Optional[str] = None


class GrantCreateSchema(BaseModel):
    grant_name: str = Field(..., min_length=1, max_length=255)
    source: Optional[str] = None
    amount_min: float = 0.0
    amount_max: Optional[float] = None
    deadline: Optional[str] = None
    income_limit: Optional[float] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    property_types: Optional[list[str]] = None
    repair_categories: Optional[list[str]] = None
    application_url: Optional[str] = None
    status: str = "open"
    description: Optional[str] = None
    agency_phone: Optional[str] = None
    agency_email: Optional[str] = None
    eligibility: Optional[EligibilityCriteriaSchema] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"open", "closing_soon", "closed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ApplicationCreateSchema(BaseModel):
    grant_id: str
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applicant_age: Optional[int] = None
    applicant_income: Optional[float] = None
    property_type: Optional[str] = None
    repair_category: Optional[str] = None
    notes: Optional[str] = None


class IntakeFormSchema(BaseModel):
    grant_id: str
    grant_name: str = ""
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    age: Optional[int] = Field(None, ge=0, le=120)
    annual_income: Optional[float] = Field(None, ge=0)
    property_type: Optional[str] = None
    repair_need: Optional[str] = None
    message: Optional[str] = Field(None, max_length=1000)


# ── Helper ────────────────────────────────────────────────────────────────────

def _grant_or_404(grant_id: str, db: Session) -> Grant:
    try:
        grant = db.query(Grant).filter(Grant.id == grant_id).first()
    except Exception:
        logger.exception("DB error fetching grant %s", grant_id)
        raise HTTPException(status_code=500, detail="Database error")
    if not grant:
        raise HTTPException(status_code=404, detail=f"Grant '{grant_id}' not found")
    return grant


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", summary="List all grants (optional status filter)")
def list_grants(
    status: Optional[str] = Query(None, description="open | closing_soon | closed"),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Grant)
        if status:
            query = query.filter(Grant.status == status)
        grants = query.order_by(Grant.grant_name).all()
        return [g.to_dict() for g in grants]
    except Exception:
        logger.exception("list_grants failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve grants")


@router.get("/match", summary="Eligibility matching — returns ranked grants with match scores")
def match_eligibility(
    age: int = Query(..., ge=0, le=120, description="Applicant age"),
    income: float = Query(..., ge=0, description="Annual household income"),
    property_type: str = Query(..., description="Property type"),
    repair_category: str = Query(..., description="Primary repair need"),
    repair_filter: Optional[str] = Query(None, description="Hard-filter by repair category"),
    include_closed: bool = Query(False),
    db: Session = Depends(get_db),
):
    if property_type not in VALID_PROPERTY_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"property_type must be one of {sorted(VALID_PROPERTY_TYPES)}",
        )
    if repair_category not in VALID_REPAIR_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"repair_category must be one of {sorted(VALID_REPAIR_CATEGORIES)}",
        )
    if repair_filter and repair_filter not in VALID_REPAIR_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"repair_filter must be one of {sorted(VALID_REPAIR_CATEGORIES)}",
        )
    results = match_grants(
        db=db,
        age=age,
        income=income,
        property_type=property_type,
        repair_category=repair_category,
        repair_filter=repair_filter,
        include_closed=include_closed,
    )
    return {"count": len(results), "results": results}


@router.get("/export/csv", summary="Export matched grants as CSV")
def export_csv(
    age: int = Query(..., ge=0, le=120),
    income: float = Query(..., ge=0),
    property_type: str = Query(...),
    repair_category: str = Query(...),
    repair_filter: Optional[str] = Query(None),
    include_closed: bool = Query(False),
    db: Session = Depends(get_db),
):
    grants = match_grants(
        db=db,
        age=age,
        income=income,
        property_type=property_type,
        repair_category=repair_category,
        repair_filter=repair_filter,
        include_closed=include_closed,
    )
    try:
        output = export_grants_csv(grants)
    except Exception:
        logger.exception("CSV export failed")
        raise HTTPException(status_code=500, detail="CSV generation failed")

    filename = f"grants_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/pdf", summary="Export matched grants as PDF")
def export_pdf(
    age: int = Query(..., ge=0, le=120),
    income: float = Query(..., ge=0),
    property_type: str = Query(...),
    repair_category: str = Query(...),
    repair_filter: Optional[str] = Query(None),
    include_closed: bool = Query(False),
    db: Session = Depends(get_db),
):
    grants = match_grants(
        db=db,
        age=age,
        income=income,
        property_type=property_type,
        repair_category=repair_category,
        repair_filter=repair_filter,
        include_closed=include_closed,
    )
    try:
        buffer = export_grants_pdf(grants)
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception:
        logger.exception("PDF export failed")
        raise HTTPException(status_code=500, detail="PDF generation failed")

    filename = f"grants_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        iter([buffer.read()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/", status_code=201, summary="Create a new grant (admin)")
def create_grant(payload: GrantCreateSchema, db: Session = Depends(get_db)):
    try:
        grant = Grant(
            grant_name=payload.grant_name,
            source=payload.source,
            amount_min=payload.amount_min,
            amount_max=payload.amount_max,
            deadline=payload.deadline,
            income_limit=payload.income_limit,
            age_min=payload.age_min,
            age_max=payload.age_max,
            property_types=json.dumps(payload.property_types) if payload.property_types else None,
            repair_categories=json.dumps(payload.repair_categories) if payload.repair_categories else None,
            application_url=payload.application_url,
            status=payload.status,
            description=payload.description,
            agency_phone=payload.agency_phone,
            agency_email=payload.agency_email,
            last_verified=datetime.utcnow(),
        )
        db.add(grant)
        db.flush()  # get the generated id

        if payload.eligibility:
            ec = EligibilityCriteria(
                grant_id=grant.id,
                **payload.eligibility.model_dump(),
            )
            db.add(ec)

        db.commit()
        db.refresh(grant)
    except Exception:
        db.rollback()
        logger.exception("Failed to create grant")
        raise HTTPException(status_code=500, detail="Failed to create grant")

    result = grant.to_dict()
    if grant.eligibility:
        result["eligibility_criteria"] = grant.eligibility.to_dict()
    return result


@router.put("/{grant_id}", summary="Update a grant (admin)")
def update_grant(grant_id: str, payload: GrantCreateSchema, db: Session = Depends(get_db)):
    grant = _grant_or_404(grant_id, db)
    try:
        grant.grant_name = payload.grant_name
        grant.source = payload.source
        grant.amount_min = payload.amount_min
        grant.amount_max = payload.amount_max
        grant.deadline = payload.deadline
        grant.income_limit = payload.income_limit
        grant.age_min = payload.age_min
        grant.age_max = payload.age_max
        grant.property_types = json.dumps(payload.property_types) if payload.property_types else None
        grant.repair_categories = json.dumps(payload.repair_categories) if payload.repair_categories else None
        grant.application_url = payload.application_url
        grant.status = payload.status
        grant.description = payload.description
        grant.agency_phone = payload.agency_phone
        grant.agency_email = payload.agency_email
        grant.last_verified = datetime.utcnow()

        if payload.eligibility:
            if grant.eligibility:
                for k, v in payload.eligibility.model_dump().items():
                    setattr(grant.eligibility, k, v)
            else:
                ec = EligibilityCriteria(grant_id=grant.id, **payload.eligibility.model_dump())
                db.add(ec)

        db.commit()
        db.refresh(grant)
    except Exception:
        db.rollback()
        logger.exception("Failed to update grant %s", grant_id)
        raise HTTPException(status_code=500, detail="Failed to update grant")

    result = grant.to_dict()
    if grant.eligibility:
        result["eligibility_criteria"] = grant.eligibility.to_dict()
    return result


@router.delete("/{grant_id}", status_code=204, summary="Delete a grant (admin)")
def delete_grant(grant_id: str, db: Session = Depends(get_db)):
    grant = _grant_or_404(grant_id, db)
    try:
        db.delete(grant)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete grant %s", grant_id)
        raise HTTPException(status_code=500, detail="Failed to delete grant")


# ── Applications sub-resource ─────────────────────────────────────────────────

@router.get("/meta/property-types", summary="Valid property types")
def get_property_types():
    return sorted(VALID_PROPERTY_TYPES)


@router.get("/meta/repair-categories", summary="Valid repair categories")
def get_repair_categories():
    return sorted(VALID_REPAIR_CATEGORIES)


@router.post("/applications/", status_code=201, summary="Submit a grant application")
def create_application(payload: ApplicationCreateSchema, db: Session = Depends(get_db)):
    _grant_or_404(payload.grant_id, db)  # validates grant exists
    try:
        app = GrantApplication(
            grant_id=payload.grant_id,
            applicant_name=payload.applicant_name,
            applicant_email=payload.applicant_email,
            applicant_age=payload.applicant_age,
            applicant_income=payload.applicant_income,
            property_type=payload.property_type,
            repair_category=payload.repair_category,
            notes=payload.notes,
        )
        db.add(app)
        db.commit()
        db.refresh(app)
    except Exception:
        db.rollback()
        logger.exception("Failed to create application")
        raise HTTPException(status_code=500, detail="Failed to create application")
    return app.to_dict()


@router.post("/intake", status_code=201, summary="Submit an interest/intake form for a grant")
def submit_intake(payload: IntakeFormSchema, db: Session = Depends(get_db)):
    """
    Lightweight intake form — stores as a GrantApplication with notes
    containing all intake fields, so no extra table is needed.
    """
    # Validate grant exists (non-fatal if missing — could be an old link)
    grant = db.query(Grant).filter(Grant.id == payload.grant_id).first()
    notes_lines = [f"INTAKE FORM — {payload.grant_name}"]
    if payload.phone:
        notes_lines.append(f"Phone: {payload.phone}")
    if payload.message:
        notes_lines.append(f"Message: {payload.message}")

    try:
        app = GrantApplication(
            grant_id=payload.grant_id,
            applicant_name=payload.full_name,
            applicant_email=payload.email,
            applicant_age=payload.age,
            applicant_income=payload.annual_income,
            property_type=payload.property_type,
            repair_category=payload.repair_need,
            notes="\n".join(notes_lines),
        )
        db.add(app)
        db.commit()
        db.refresh(app)
    except Exception:
        db.rollback()
        logger.exception("Failed to save intake form")
        raise HTTPException(status_code=500, detail="Failed to save intake form")

    return {"status": "received", "application_id": app.id, "grant_id": payload.grant_id}


@router.get("/{grant_id}/applications", summary="List applications for a grant")
def list_applications(grant_id: str, db: Session = Depends(get_db)):
    _grant_or_404(grant_id, db)
    try:
        apps = db.query(GrantApplication).filter(GrantApplication.grant_id == grant_id).all()
        return [a.to_dict() for a in apps]
    except Exception:
        logger.exception("Failed to list applications for grant %s", grant_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve applications")


@router.get("/{grant_id}", summary="Get a single grant by ID")
def get_grant(grant_id: str, db: Session = Depends(get_db)):
    grant = _grant_or_404(grant_id, db)
    result = grant.to_dict()
    if grant.eligibility:
        result["eligibility_criteria"] = grant.eligibility.to_dict()
    return result
