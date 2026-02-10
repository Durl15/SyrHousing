from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from ..database import get_db
from ..auth import require_admin
from ..models.user import User
from ..models.application import Application
from ..models.application_history import ApplicationStatusHistory
from ..models.program import Program
from ..schemas.admin import AdminStatsResponse, UserAdminUpdate, UserListItem
from ..schemas.application import ApplicationRead, ApplicationStatusChange
from ..schemas.auth import UserRead
from ..services.email import send_application_submitted, send_application_status_update

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _app_to_read(app: Application, db: Session) -> dict:
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


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar()
    total_apps = db.query(func.count(Application.id)).scalar()
    active_programs = db.query(func.count(Program.id)).filter(Program.is_active == True).scalar()

    # Applications by status
    status_rows = db.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    by_status = {s: c for s, c in status_rows}

    # Recent registrations (last 30 days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent = db.query(func.count(User.id)).filter(User.created_at >= cutoff).scalar()

    return AdminStatsResponse(
        total_users=total_users,
        total_applications=total_apps,
        applications_by_status=by_status,
        active_programs=active_programs,
        recent_registrations=recent,
    )


@router.get("/chart-data")
def get_chart_data(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Programs by category
    cat_rows = db.query(Program.menu_category, func.count(Program.id)).filter(
        Program.is_active == True
    ).group_by(Program.menu_category).all()
    programs_by_category = [{"name": c, "count": n} for c, n in cat_rows if c]

    # Applications by status
    status_rows = db.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    apps_by_status = [{"name": s.replace("_", " ").title(), "count": n} for s, n in status_rows]

    # User registrations over last 12 weeks
    reg_trend = []
    now = datetime.now(timezone.utc)
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = db.query(func.count(User.id)).filter(
            User.created_at >= week_start, User.created_at < week_end
        ).scalar()
        label = week_end.strftime("%b %d")
        reg_trend.append({"week": label, "users": count})

    # Applications over last 12 weeks
    app_trend = []
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = db.query(func.count(Application.id)).filter(
            Application.created_at >= week_start, Application.created_at < week_end
        ).scalar()
        label = week_end.strftime("%b %d")
        app_trend.append({"week": label, "applications": count})

    # Top 10 programs by score (for user dashboard)
    from ..services.ranking import compute_rank
    from ..models.user_profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.profile_name == "default", UserProfile.user_id.is_(None)).first()
    score_data = []
    if profile:
        programs = db.query(Program).filter(Program.is_active == True).all()
        for p in programs:
            score, _ = compute_rank(p, profile)
            score_data.append({"name": p.name[:25], "score": score})
        score_data.sort(key=lambda x: x["score"], reverse=True)
        score_data = score_data[:10]

    # Scan status distribution
    from ..models.scan import ScanState
    scan_rows = db.query(ScanState.status, func.count(ScanState.program_key)).group_by(ScanState.status).all()
    scan_status = [{"name": s, "count": n} for s, n in scan_rows]

    return {
        "programs_by_category": programs_by_category,
        "apps_by_status": apps_by_status,
        "registration_trend": reg_trend,
        "application_trend": app_trend,
        "top_scores": score_data,
        "scan_status": scan_status,
    }


@router.get("/users", response_model=List[UserListItem])
def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if search:
        pattern = f"%{search}%"
        q = q.filter(User.email.ilike(pattern) | User.full_name.ilike(pattern))
    if role:
        q = q.filter(User.role == role)
    if active_only:
        q = q.filter(User.is_active == True)

    users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for u in users:
        app_count = db.query(func.count(Application.id)).filter(Application.user_id == u.id).scalar()
        result.append(UserListItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at,
            application_count=app_count,
        ))
    return result


@router.get("/users/{user_id}", response_model=UserRead)
def get_user_detail(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    data: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None and data.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/applications", response_model=List[ApplicationRead])
def list_all_applications(
    status: Optional[str] = None,
    program_key: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Application)
    if status:
        q = q.filter(Application.status == status)
    if program_key:
        q = q.filter(Application.program_key == program_key)
    if user_id:
        q = q.filter(Application.user_id == user_id)

    apps = q.order_by(Application.updated_at.desc()).offset(skip).limit(limit).all()
    return [_app_to_read(a, db) for a in apps]


@router.post("/applications/{application_id}/status", response_model=ApplicationRead)
def admin_change_status(
    application_id: str,
    data: ApplicationStatusChange,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    valid = {"draft", "submitted", "under_review", "approved", "denied", "withdrawn"}
    if data.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(sorted(valid))}")

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

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
        changed_by=admin_user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(app)

    # Notify the application owner
    result = _app_to_read(app, db)
    app_owner = app.user
    if app_owner and data.status != old_status:
        if data.status == "submitted":
            send_application_submitted(app_owner.email, app_owner.full_name, result["program_name"])
        elif data.status in ("under_review", "approved", "denied", "withdrawn"):
            send_application_status_update(
                app_owner.email, app_owner.full_name, result["program_name"], data.status, data.notes
            )

    return result
