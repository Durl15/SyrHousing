"""
Export API endpoints for generating PDF and CSV reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.program import Program
from ..models.user_profile import UserProfile
from ..services.export import (
    generate_csv_export,
    generate_pdf_report,
    generate_application_checklist_pdf
)
from ..services.ranking import compute_rank

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
def export_programs_csv(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    profile_name: Optional[str] = Query("default", description="Profile for matching"),
    min_score: Optional[int] = Query(0, description="Minimum match score (0-100)"),
):
    """
    Export programs to CSV format.
    Optionally filter by category and match score.
    """
    try:
        # Get profile if specified
        profile = None
        if profile_name:
            profile = db.query(UserProfile).filter(
                UserProfile.profile_name == profile_name
            ).first()

        # Query programs
        query = db.query(Program).filter(Program.is_active == True)

        if category:
            query = query.filter(Program.menu_category == category)

        programs = query.all()

        # Filter by match score if profile provided
        if profile and min_score > 0:
            filtered_programs = []
            for program in programs:
                score, _ = compute_rank(program, profile)
                if score >= min_score:
                    filtered_programs.append(program)
            programs = filtered_programs

        # Generate CSV
        csv_content = generate_csv_export(programs, profile)

        # Return as downloadable file
        filename = f"syracuse_grants_{category or 'all'}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/pdf")
def export_programs_pdf(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    profile_name: Optional[str] = Query("default", description="Profile for matching"),
    min_score: Optional[int] = Query(0, description="Minimum match score (0-100)"),
    title: Optional[str] = Query("Syracuse Housing Grant Report", description="Report title"),
):
    """
    Export programs to PDF format.
    Includes detailed information and match scores.
    """
    try:
        # Get profile if specified
        profile = None
        if profile_name:
            profile = db.query(UserProfile).filter(
                UserProfile.profile_name == profile_name
            ).first()

        # Query programs
        query = db.query(Program).filter(Program.is_active == True)

        if category:
            query = query.filter(Program.menu_category == category)

        programs = query.all()

        # Filter by match score if profile provided
        if profile and min_score > 0:
            filtered_programs = []
            for program in programs:
                score, _ = compute_rank(program, profile)
                if score >= min_score:
                    filtered_programs.append(program)
            programs = filtered_programs

        if not programs:
            raise HTTPException(
                status_code=404,
                detail="No programs found matching the specified criteria"
            )

        # Generate PDF
        pdf_bytes = generate_pdf_report(programs, profile, title)

        # Return as downloadable file
        filename = f"syracuse_grants_{category or 'all'}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/pdf/checklist/{program_key}")
def export_application_checklist(
    program_key: str,
    db: Session = Depends(get_db),
    profile_name: Optional[str] = Query("default", description="Profile for matching"),
):
    """
    Export application checklist PDF for a specific program.
    Includes all required documents and application steps.
    """
    try:
        # Get program
        program = db.query(Program).filter(
            Program.program_key == program_key,
            Program.is_active == True
        ).first()

        if not program:
            raise HTTPException(status_code=404, detail="Program not found")

        # Get profile if specified
        profile = None
        if profile_name:
            profile = db.query(UserProfile).filter(
                UserProfile.profile_name == profile_name
            ).first()

        # Generate checklist PDF
        pdf_bytes = generate_application_checklist_pdf(program, profile)

        # Return as downloadable file
        filename = f"checklist_{program.program_key}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/pdf/matching-grants")
def export_matching_grants_pdf(
    db: Session = Depends(get_db),
    profile_name: str = Query("default", description="Profile name"),
    min_score: int = Query(50, description="Minimum match score"),
):
    """
    Export PDF of all grants matching user profile above minimum score.
    Sorted by match score (highest first).
    """
    try:
        # Get profile
        profile = db.query(UserProfile).filter(
            UserProfile.profile_name == profile_name
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Get all active programs
        programs = db.query(Program).filter(Program.is_active == True).all()

        # Filter and sort by match score
        matching_programs = []
        for program in programs:
            score, _ = compute_rank(program, profile)
            if score >= min_score:
                matching_programs.append((score, program))

        matching_programs.sort(key=lambda x: x[0], reverse=True)
        filtered_programs = [p for _, p in matching_programs]

        if not filtered_programs:
            raise HTTPException(
                status_code=404,
                detail=f"No programs found with match score >= {min_score}"
            )

        # Generate PDF
        title = f"Your Matching Grants (Score {min_score}+)"
        pdf_bytes = generate_pdf_report(filtered_programs, profile, title)

        # Return as downloadable file
        filename = f"matching_grants_{profile_name}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
