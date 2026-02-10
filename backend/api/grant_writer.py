"""
Grant writer API endpoints.
Provides AI-powered grant application writing assistance.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.application import Application
from ..models.user_profile import UserProfile
from ..models.program import Program
from ..schemas.grant_writer import (
    GenerateRequest,
    GenerateResponse,
    RefineRequest,
    DraftResponse,
)
from ..services import grant_writer

router = APIRouter(prefix="/api/grant-writer", tags=["grant-writer"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(
    body: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate grant application content using AI.

    Supports generating:
    - cover_letter: Professional introduction and expression of need
    - eligibility_statement: Point-by-point matching to program requirements
    - project_description: Detailed narrative of repair needs
    - needs_justification: Explanation of financial need
    """
    # Verify application ownership
    app = db.query(Application).filter(
        Application.id == body.application_id,
        Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        # Try to get default profile
        profile = db.query(UserProfile).filter(UserProfile.profile_name == "default").first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Please create a profile first.")

    # Generate content based on type
    try:
        if body.content_type == "cover_letter":
            content, used_llm = grant_writer.generate_cover_letter(db, body.application_id, profile)
        elif body.content_type == "eligibility_statement":
            content, used_llm = grant_writer.generate_eligibility_statement(db, body.application_id, profile)
        elif body.content_type == "project_description":
            content, used_llm = grant_writer.generate_project_description(db, body.application_id, profile)
        elif body.content_type == "needs_justification":
            content, used_llm = grant_writer.generate_needs_justification(db, body.application_id, profile)
        else:
            raise HTTPException(status_code=400, detail="Invalid content type. Must be: cover_letter, eligibility_statement, project_description, or needs_justification")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

    # Save to application.notes
    try:
        notes = json.loads(app.notes) if app.notes else {}
    except (json.JSONDecodeError, TypeError):
        notes = {}

    version = notes.get(body.content_type, {}).get("version", 0) + 1

    notes[body.content_type] = {
        "content": content,
        "generated_at": datetime.utcnow().isoformat(),
        "version": version,
        "used_llm": used_llm
    }

    app.notes = json.dumps(notes)
    db.commit()

    return GenerateResponse(
        content=content,
        used_llm=used_llm,
        generated_at=datetime.utcnow(),
        version=version
    )


@router.get("/drafts/{application_id}", response_model=DraftResponse)
async def get_drafts(
    application_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all saved drafts for an application.

    Returns the complete drafts dictionary from Application.notes.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    try:
        drafts = json.loads(app.notes) if app.notes else {}
    except (json.JSONDecodeError, TypeError):
        drafts = {}

    return DraftResponse(drafts=drafts)


@router.post("/refine", response_model=GenerateResponse)
async def refine_content(
    body: RefineRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refine existing content based on user feedback.

    Uses AI to improve the content according to user's suggestions.
    Falls back to returning original content if LLM unavailable.
    """
    # Verify application ownership
    app = db.query(Application).filter(
        Application.id == body.application_id,
        Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get user profile and program for context
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = db.query(UserProfile).filter(UserProfile.profile_name == "default").first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    program = db.query(Program).filter(Program.program_key == app.program_key).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Refine content
    try:
        # For now, just return the current content with a note
        # Full refinement implementation would use grant_writer.refine_content()
        content = body.current_content + "\n\n[Note: Refinement feature coming soon]"
        used_llm = False
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refine content: {str(e)}")

    # Save refined version
    try:
        notes = json.loads(app.notes) if app.notes else {}
    except (json.JSONDecodeError, TypeError):
        notes = {}

    version = notes.get(body.content_type, {}).get("version", 0) + 1

    notes[body.content_type] = {
        "content": content,
        "generated_at": datetime.utcnow().isoformat(),
        "version": version,
        "used_llm": used_llm
    }

    app.notes = json.dumps(notes)
    db.commit()

    return GenerateResponse(
        content=content,
        used_llm=used_llm,
        generated_at=datetime.utcnow(),
        version=version
    )
