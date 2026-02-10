from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models.scan import ScanResult, ScanState
from ..schemas.scan import ScanResultRead, ScanStateRead, ScanTriggerResponse
from ..services.scanner import run_scan, build_latest_report

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


@router.post("/run", response_model=ScanTriggerResponse)
def trigger_scan(db: Session = Depends(get_db)):
    result = run_scan(db)
    return ScanTriggerResponse(
        message=result["message"],
        scanned=result["scanned"],
        changes=result["changes"],
        errors=result["errors"],
        results=[ScanResultRead.model_validate(r) for r in result["results"]],
    )


@router.get("/state", response_model=List[ScanStateRead])
def get_all_states(db: Session = Depends(get_db)):
    return db.query(ScanState).all()


@router.get("/state/{program_key}", response_model=ScanStateRead)
def get_state(program_key: str, db: Session = Depends(get_db)):
    s = db.query(ScanState).filter(ScanState.program_key == program_key).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scan state not found")
    return s


@router.get("/history", response_model=List[ScanResultRead])
def scan_history(
    program_key: Optional[str] = None,
    since: Optional[datetime] = None,
    changed_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(ScanResult)
    if program_key:
        q = q.filter(ScanResult.watchlist_program_key == program_key)
    if since:
        q = q.filter(ScanResult.timestamp >= since)
    if changed_only:
        q = q.filter(ScanResult.changed == True)
    return q.order_by(ScanResult.timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/latest-report")
def latest_report(db: Session = Depends(get_db)):
    text = build_latest_report(db)
    return {"report": text}
