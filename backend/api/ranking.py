from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from ..database import get_db
from ..models.program import Program
from ..models.user_profile import UserProfile
from ..schemas.ranking import RankRequest, RankResult, RankResponse
from ..schemas.program import ProgramWithRank
from ..services.ranking import compute_rank

router = APIRouter(prefix="/api/ranking", tags=["ranking"])


def _get_profile(db: Session, profile_id: Optional[str]) -> UserProfile:
    if profile_id:
        p = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Profile not found")
        return p
    p = db.query(UserProfile).filter(UserProfile.profile_name == "default").first()
    if not p:
        raise HTTPException(status_code=404, detail="No default profile found")
    return p


@router.get("/ranked-programs", response_model=List[ProgramWithRank])
def ranked_programs(
    profile_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    profile = _get_profile(db, profile_id)
    programs = db.query(Program).filter(Program.is_active == True).all()
    results = []
    for p in programs:
        score, why = compute_rank(p, profile)
        results.append(ProgramWithRank(
            **{c.name: getattr(p, c.name) for c in p.__table__.columns},
            computed_score=score,
            rank_explanation=why,
        ))
    results.sort(key=lambda x: x.computed_score, reverse=True)
    return results


@router.post("/compute", response_model=RankResponse)
def compute_rankings(body: RankRequest, db: Session = Depends(get_db)):
    profile = _get_profile(db, body.profile_id)
    q = db.query(Program).filter(Program.is_active == True)
    if body.program_keys:
        q = q.filter(Program.program_key.in_(body.program_keys))
    programs = q.all()

    rank_results = []
    for p in programs:
        score, why = compute_rank(p, profile)
        rank_results.append(RankResult(
            program_key=p.program_key,
            name=p.name,
            menu_category=p.menu_category,
            computed_score=score,
            explanation=why,
        ))
    rank_results.sort(key=lambda x: x.computed_score, reverse=True)
    return RankResponse(profile_id=profile.id, results=rank_results)


@router.get("/chart-data")
def ranking_chart_data(
    profile_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Chart-ready data: score distribution, category breakdown, top programs."""
    profile = _get_profile(db, profile_id)
    programs = db.query(Program).filter(Program.is_active == True).all()

    # Top 10 by score
    scored = []
    for p in programs:
        score, _ = compute_rank(p, profile)
        scored.append({"name": p.name[:30], "score": score, "category": p.menu_category})
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Score distribution buckets
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scored:
        v = s["score"]
        if v <= 20: buckets["0-20"] += 1
        elif v <= 40: buckets["21-40"] += 1
        elif v <= 60: buckets["41-60"] += 1
        elif v <= 80: buckets["61-80"] += 1
        else: buckets["81-100"] += 1
    score_distribution = [{"range": k, "count": v} for k, v in buckets.items()]

    # Programs by category
    cat_rows = db.query(Program.menu_category, func.count(Program.id)).filter(
        Program.is_active == True
    ).group_by(Program.menu_category).all()
    by_category = [{"name": c, "count": n} for c, n in cat_rows if c]

    return {
        "top_programs": scored[:10],
        "score_distribution": score_distribution,
        "programs_by_category": by_category,
    }
