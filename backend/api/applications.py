from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.application import Application
from ..models.application_history import ApplicationStatusHistory
from ..models.program import Program
from ..schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationStatusChange,
    ApplicationRead, ApplicationDetail, StatusHistoryRead,
)
from ..services.email import send_application_submitted, send_application_status_update

router = APIRouter(prefix="/api/applications", tags=["applications"])

VALID_STATUSES = {"draft", "submitted", "under_review", "approved", "denied", "withdrawn"}


def _to_read(app: Application, db: Session) -> dict:
    """Convert Application ORM to dict with program_name."""
    prog = db.query(Program).filter(Program.program_key == app.program_key).first()
    return {
        "id": app.id,
        "user_id": app.user_id,
        "program_key": app.program_key,
        "program_name": prog.name if prog else app.program_key,
        "status": app.status,
        "notes": app.notes,
        "documents_checklist": app.documents_checklist,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
        "applied_at": app.applied_at,
        "decided_at": app.decided_at,
    }


@router.get("", response_model=List[ApplicationRead])
def list_my_applications(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Application).filter(Application.user_id == user.id)
    if status:
        q = q.filter(Application.status == status)
    apps = q.order_by(Application.updated_at.desc()).offset(skip).limit(limit).all()
    return [_to_read(a, db) for a in apps]


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(
    data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify program exists
    prog = db.query(Program).filter(Program.program_key == data.program_key).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found")

    # Check for duplicate
    existing = db.query(Application).filter(
        Application.user_id == user.id,
        Application.program_key == data.program_key,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Application already exists for this program")

    app = Application(
        user_id=user.id,
        program_key=data.program_key,
        notes=data.notes or None,
        status="draft",
    )
    db.add(app)
    db.flush()

    # Record initial status
    history = ApplicationStatusHistory(
        application_id=app.id,
        from_status=None,
        to_status="draft",
        notes="Application created",
    )
    db.add(history)
    db.commit()
    db.refresh(app)
    return _to_read(app, db)


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    result = _to_read(app, db)
    result["status_history"] = [
        StatusHistoryRead.model_validate(h) for h in app.status_history
    ]
    return result


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: str,
    data: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return _to_read(app, db)


@router.post("/{application_id}/status", response_model=ApplicationRead)
def change_status(
    application_id: str,
    data: ApplicationStatusChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}")

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    old_status = app.status
    app.status = data.status

    now = datetime.now(timezone.utc)
    if data.status == "submitted" and not app.applied_at:
        app.applied_at = now
    if data.status in ("approved", "denied"):
        app.decided_at = now

    history = ApplicationStatusHistory(
        application_id=app.id,
        from_status=old_status,
        to_status=data.status,
        notes=data.notes,
        changed_by=user.id if user.role == "admin" and app.user_id != user.id else None,
    )
    db.add(history)
    db.commit()
    db.refresh(app)

    # Send email notification
    result = _to_read(app, db)
    app_user = app.user
    if app_user and data.status != old_status:
        if data.status == "submitted":
            send_application_submitted(app_user.email, app_user.full_name, result["program_name"])
        elif data.status in ("under_review", "approved", "denied", "withdrawn"):
            send_application_status_update(
                app_user.email, app_user.full_name, result["program_name"], data.status, data.notes
            )

    return result
