from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
import re
from ..database import get_db
from ..auth import require_admin
from ..models.user import User
from ..models.program import Program
from ..schemas.program import ProgramCreate, ProgramUpdate, ProgramRead

router = APIRouter(prefix="/api/programs", tags=["programs"])


@router.get("", response_model=List[ProgramRead])
def list_programs(
    # Existing filters
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = True,

    # New advanced filters
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    program_type: Optional[str] = Query(None, description="Filter by program type (grant, loan, etc)"),
    min_benefit: Optional[int] = Query(None, description="Minimum benefit amount"),
    max_benefit: Optional[int] = Query(None, description="Maximum benefit amount"),
    has_deadline: Optional[bool] = Query(None, description="Filter by presence of deadline"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),

    # Sorting
    sort_by: Optional[str] = Query("priority", description="Sort by: priority, name, deadline, benefit, recent"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),

    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),

    db: Session = Depends(get_db),
):
    """
    Enhanced program listing with advanced search and filtering.

    Features:
    - Full-text search across name, agency, eligibility, tags
    - Multi-category filtering
    - Program type filtering (grant, loan, etc)
    - Benefit amount range filtering
    - Jurisdiction filtering
    - Multiple sort options
    """
    q = db.query(Program)

    # Active filter
    if active_only:
        q = q.filter(Program.is_active == True)

    # Multi-category filter (new)
    if categories:
        category_list = [c.strip() for c in categories.split(",") if c.strip()]
        if category_list:
            category_filters = [Program.menu_category.ilike(f"%{cat}%") for cat in category_list]
            q = q.filter(or_(*category_filters))
    # Single category (backward compatibility)
    elif category:
        q = q.filter(Program.menu_category.ilike(f"%{category}%"))

    # Tag filter
    if tag:
        q = q.filter(Program.repair_tags.ilike(f"%{tag}%"))

    # Program type filter (new)
    if program_type:
        q = q.filter(Program.program_type.ilike(f"%{program_type}%"))

    # Jurisdiction filter (new)
    if jurisdiction:
        q = q.filter(
            or_(
                Program.jurisdiction.ilike(f"%{jurisdiction}%"),
                Program.agency.ilike(f"%{jurisdiction}%")
            )
        )

    # Deadline filter (new)
    if has_deadline is not None:
        if has_deadline:
            q = q.filter(Program.status_or_deadline.isnot(None))
            q = q.filter(Program.status_or_deadline != "")
        else:
            q = q.filter(
                or_(
                    Program.status_or_deadline.is_(None),
                    Program.status_or_deadline == ""
                )
            )

    # Full-text search (enhanced)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                Program.name.ilike(pattern),
                Program.agency.ilike(pattern),
                Program.eligibility_summary.ilike(pattern),
                Program.income_guidance.ilike(pattern),
                Program.repair_tags.ilike(pattern),
                Program.program_type.ilike(pattern),
                Program.docs_checklist.ilike(pattern)
            )
        )

    # Benefit amount filtering (new)
    # Note: max_benefit is stored as text, we'll do basic pattern matching
    if min_benefit is not None or max_benefit is not None:
        programs = q.all()
        filtered = []
        for prog in programs:
            if prog.max_benefit:
                # Extract numbers from benefit text
                numbers = re.findall(r'\$?[\d,]+', prog.max_benefit)
                if numbers:
                    # Get the largest number found
                    amounts = []
                    for num in numbers:
                        clean_num = num.replace('$', '').replace(',', '')
                        try:
                            amounts.append(int(clean_num))
                        except ValueError:
                            continue
                    if amounts:
                        benefit_amount = max(amounts)
                        if min_benefit and benefit_amount < min_benefit:
                            continue
                        if max_benefit and benefit_amount > max_benefit:
                            continue
                filtered.append(prog)
        programs = filtered
    else:
        programs = q.all()

    # Sorting (new)
    if sort_by == "name":
        programs.sort(key=lambda p: p.name.lower())
    elif sort_by == "benefit":
        def get_benefit_value(prog):
            if not prog.max_benefit:
                return 0
            numbers = re.findall(r'\$?[\d,]+', prog.max_benefit)
            if numbers:
                try:
                    return max([int(n.replace('$', '').replace(',', '')) for n in numbers])
                except:
                    return 0
            return 0
        programs.sort(key=get_benefit_value)
    elif sort_by == "recent":
        programs.sort(key=lambda p: p.created_at if p.created_at else p.updated_at)
    elif sort_by == "deadline":
        # Sort by presence of deadline
        programs.sort(key=lambda p: (p.status_or_deadline or "zzz"))
    else:  # priority (default)
        programs.sort(key=lambda p: p.priority_rank)

    # Apply sort order
    if sort_order == "asc":
        pass  # Already sorted ascending
    else:  # desc
        programs.reverse()

    # Pagination
    return programs[skip:skip + limit]


@router.get("/tags", response_model=List[str])
def list_tags(db: Session = Depends(get_db)):
    rows = db.query(Program.repair_tags).filter(
        Program.is_active == True, Program.repair_tags.isnot(None)
    ).all()
    tags = set()
    for (rt,) in rows:
        if rt:
            for t in rt.split(";"):
                t = t.strip().lower()
                if t:
                    tags.add(t)
    return sorted(tags)


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Program.menu_category).filter(
        Program.is_active == True
    ).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@router.get("/{program_key}", response_model=ProgramRead)
def get_program(program_key: str, db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.program_key == program_key).first()
    if not p:
        raise HTTPException(status_code=404, detail="Program not found")
    return p


@router.post("", response_model=ProgramRead, status_code=201)
def create_program(data: ProgramCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    existing = db.query(Program).filter(Program.program_key == data.program_key).first()
    if existing:
        raise HTTPException(status_code=409, detail="program_key already exists")
    p = Program(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{program_key}", response_model=ProgramRead)
def update_program(program_key: str, data: ProgramUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.program_key == program_key).first()
    if not p:
        raise HTTPException(status_code=404, detail="Program not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{program_key}", status_code=204)
def delete_program(program_key: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.program_key == program_key).first()
    if not p:
        raise HTTPException(status_code=404, detail="Program not found")
    p.is_active = False
    db.commit()
