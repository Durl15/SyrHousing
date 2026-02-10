"""
API endpoints for automated grant discovery.
Admin-only endpoints for managing grant discovery runs and reviewing discovered grants.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
import uuid
from datetime import datetime, timezone

from ..database import get_db
from ..auth import require_admin
from ..models.user import User
from ..models.discovered_grant import DiscoveredGrant, DiscoveryRun
from ..models.program import Program
from ..schemas.discovery import (
    DiscoveredGrantRead,
    DiscoveryRunRead,
    DiscoveryRunDetail,
    TriggerDiscoveryRequest,
    ApproveGrantRequest,
    RejectGrantRequest,
    MarkDuplicateRequest,
    DiscoveryStats
)
from ..services.discovery.discovery_service import (
    run_discovery,
    approve_discovered_grant,
    get_high_confidence_grants
)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.post("/run", response_model=DiscoveryRunRead)
def trigger_discovery(
    request: TriggerDiscoveryRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Trigger a manual grant discovery run.

    Fetches grants from configured sources, extracts data, checks for duplicates,
    and saves discovered grants for admin review.

    **Admin only**
    """
    try:
        run = run_discovery(
            db=db,
            sources=request.sources,
            send_notification=request.send_notification
        )
        return run
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery run failed: {str(e)}")


@router.get("/runs", response_model=List[DiscoveryRunRead])
def list_discovery_runs(
    status: Optional[str] = Query(None, description="Filter by status: running, completed, completed_with_errors, failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    List past discovery runs with statistics.

    Returns runs sorted by most recent first.

    **Admin only**
    """
    query = db.query(DiscoveryRun)

    if status:
        query = query.filter(DiscoveryRun.status == status)

    runs = query.order_by(desc(DiscoveryRun.started_at)).offset(skip).limit(limit).all()
    return runs


@router.get("/runs/{run_id}", response_model=DiscoveryRunDetail)
def get_discovery_run(
    run_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get detailed information about a specific discovery run.

    Includes error log for troubleshooting.

    **Admin only**
    """
    run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Discovery run not found")

    return run


@router.get("/grants", response_model=List[DiscoveredGrantRead])
def list_discovered_grants(
    status: Optional[str] = Query(None, description="Filter by review status: pending, approved, rejected, duplicate"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    source_type: Optional[str] = Query(None, description="Filter by source: rss_feed, grants_gov_api, web_scrape"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    search: Optional[str] = Query(None, description="Search in grant name and agency"),
    sort_by: Optional[str] = Query("confidence", description="Sort by: confidence, discovered_at, name"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    List discovered grants with filtering and sorting.

    Use this endpoint to review pending grants, check high-confidence discoveries,
    or audit past approvals/rejections.

    **Admin only**
    """
    query = db.query(DiscoveredGrant)

    # Apply filters
    if status:
        query = query.filter(DiscoveredGrant.review_status == status)

    if min_confidence is not None:
        query = query.filter(DiscoveredGrant.confidence_score >= min_confidence)

    if source_type:
        query = query.filter(DiscoveredGrant.source_type == source_type)

    if jurisdiction:
        query = query.filter(DiscoveredGrant.jurisdiction == jurisdiction)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (DiscoveredGrant.name.ilike(search_term)) |
            (DiscoveredGrant.agency.ilike(search_term))
        )

    # Apply sorting
    if sort_by == "confidence":
        order_col = DiscoveredGrant.confidence_score
    elif sort_by == "discovered_at":
        order_col = DiscoveredGrant.discovered_at
    elif sort_by == "name":
        order_col = DiscoveredGrant.name
    else:
        order_col = DiscoveredGrant.confidence_score

    if sort_order == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    grants = query.offset(skip).limit(limit).all()
    return grants


@router.get("/grants/{grant_id}", response_model=DiscoveredGrantRead)
def get_discovered_grant(
    grant_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get detailed information about a specific discovered grant.

    **Admin only**
    """
    grant = db.query(DiscoveredGrant).filter(DiscoveredGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Discovered grant not found")

    return grant


@router.post("/grants/{grant_id}/approve", response_model=dict)
def approve_grant(
    grant_id: str,
    request: ApproveGrantRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Approve a discovered grant and optionally create a Program record.

    If create_program=True, creates a new Program with the discovered data.
    You can provide overrides for any Program fields in the request.

    **Admin only**
    """
    grant = db.query(DiscoveredGrant).filter(DiscoveredGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Discovered grant not found")

    if grant.review_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Grant already reviewed (status: {grant.review_status})"
        )

    try:
        # If overrides provided, apply them before approval
        if request.name:
            grant.name = request.name
        if request.jurisdiction:
            grant.jurisdiction = request.jurisdiction
        if request.program_type:
            grant.program_type = request.program_type
        if request.max_benefit:
            grant.max_benefit = request.max_benefit
        if request.status_or_deadline:
            grant.status_or_deadline = request.status_or_deadline
        if request.agency:
            grant.agency = request.agency
        if request.phone:
            grant.phone = request.phone
        if request.email:
            grant.email = request.email
        if request.website:
            grant.website = request.website
        if request.eligibility_summary:
            grant.eligibility_summary = request.eligibility_summary
        if request.docs_checklist:
            grant.docs_checklist = request.docs_checklist

        # Approve and create program
        program = approve_discovered_grant(
            db=db,
            grant_id=grant_id,
            admin_user_id=admin.id,
            create_program=request.create_program,
            program_key=request.program_key
        )

        # Apply additional overrides to program if provided
        if program and request.menu_category:
            program.menu_category = request.menu_category
        if program and request.priority_rank is not None:
            program.priority_rank = request.priority_rank

        if program:
            db.commit()

        return {
            "message": "Grant approved successfully",
            "program_key": program.program_key if program else None,
            "program_id": program.id if program else None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.post("/grants/{grant_id}/reject", response_model=dict)
def reject_grant(
    grant_id: str,
    request: RejectGrantRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Reject a discovered grant with a reason.

    The grant will be marked as rejected and will not appear in pending reviews.

    **Admin only**
    """
    grant = db.query(DiscoveredGrant).filter(DiscoveredGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Discovered grant not found")

    if grant.review_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Grant already reviewed (status: {grant.review_status})"
        )

    try:
        grant.review_status = "rejected"
        grant.reviewed_by = admin.id
        grant.reviewed_at = datetime.now(timezone.utc)
        grant.review_notes = request.reason

        db.commit()

        return {
            "message": "Grant rejected successfully",
            "grant_id": grant_id,
            "reason": request.reason
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")


@router.post("/grants/{grant_id}/mark-duplicate", response_model=dict)
def mark_as_duplicate(
    grant_id: str,
    request: MarkDuplicateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Mark a discovered grant as a duplicate of an existing program.

    This should be used when the automated deduplication missed a duplicate,
    or when you want to manually link a grant to an existing program.

    **Admin only**
    """
    grant = db.query(DiscoveredGrant).filter(DiscoveredGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Discovered grant not found")

    if grant.review_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Grant already reviewed (status: {grant.review_status})"
        )

    # Verify program exists
    program = db.query(Program).filter(Program.program_key == request.program_key).first()
    if not program:
        raise HTTPException(status_code=404, detail=f"Program '{request.program_key}' not found")

    try:
        grant.review_status = "duplicate"
        grant.reviewed_by = admin.id
        grant.reviewed_at = datetime.now(timezone.utc)
        grant.matched_program_key = request.program_key
        grant.review_notes = request.notes or f"Manually marked as duplicate of {request.program_key}"

        db.commit()

        return {
            "message": "Grant marked as duplicate successfully",
            "grant_id": grant_id,
            "matched_program": request.program_key
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to mark as duplicate: {str(e)}")


@router.get("/stats", response_model=DiscoveryStats)
def get_discovery_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get summary statistics for the discovery system.

    Useful for monitoring system health and performance.

    **Admin only**
    """
    # Run statistics
    total_runs = db.query(func.count(DiscoveryRun.id)).scalar() or 0
    total_discovered = db.query(func.sum(DiscoveryRun.grants_discovered)).scalar() or 0
    total_duplicates = db.query(func.sum(DiscoveryRun.duplicates_found)).scalar() or 0

    # Grant statistics by status
    pending_review = db.query(func.count(DiscoveredGrant.id)).filter(
        DiscoveredGrant.review_status == "pending"
    ).scalar() or 0

    approved = db.query(func.count(DiscoveredGrant.id)).filter(
        DiscoveredGrant.review_status == "approved"
    ).scalar() or 0

    rejected = db.query(func.count(DiscoveredGrant.id)).filter(
        DiscoveredGrant.review_status == "rejected"
    ).scalar() or 0

    # Average confidence score
    avg_confidence = db.query(func.avg(DiscoveredGrant.confidence_score)).scalar() or 0.0

    # Last run
    last_run = db.query(DiscoveryRun).order_by(desc(DiscoveryRun.started_at)).first()
    last_run_at = last_run.started_at if last_run else None

    return DiscoveryStats(
        total_runs=total_runs,
        total_discovered=total_discovered,
        total_duplicates=total_duplicates,
        pending_review=pending_review,
        approved=approved,
        rejected=rejected,
        avg_confidence=float(avg_confidence),
        last_run_at=last_run_at
    )


@router.get("/high-confidence", response_model=List[DiscoveredGrantRead])
def get_high_confidence(
    min_confidence: float = Query(0.8, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get high-confidence discovered grants pending review.

    These grants have high data quality and are good candidates for quick approval.

    **Admin only**
    """
    grants = get_high_confidence_grants(db, min_confidence=min_confidence)
    return grants[:limit]
