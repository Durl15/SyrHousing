from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from ..models.user_profile import UserProfile
from ..models.program import Program
from ..schemas.ai import (
    AIChatRequest, AIChatResponse,
    EligibilityScreenRequest, EligibilityScreenResponse,
    AIStatusResponse,
)
from ..services.eligibility import ai_chat, screen_eligibility
from ..services.llm import is_llm_available

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _get_profile(db: Session, profile_id: str | None) -> UserProfile:
    if profile_id:
        p = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Profile not found")
        return p
    p = db.query(UserProfile).filter(UserProfile.profile_name == "default").first()
    if not p:
        raise HTTPException(status_code=404, detail="No default profile found")
    return p


@router.get("/status", response_model=AIStatusResponse)
def ai_status():
    provider = settings.LLM_PROVIDER if is_llm_available() else "none"
    model = ""
    if provider == "anthropic":
        model = settings.ANTHROPIC_MODEL
    elif provider == "openai":
        model = settings.OPENAI_MODEL
    return AIStatusResponse(
        llm_available=is_llm_available(),
        provider=provider,
        model=model,
    )


@router.post("/chat", response_model=AIChatResponse)
def chat(body: AIChatRequest, db: Session = Depends(get_db)):
    profile = _get_profile(db, body.profile_id)

    try:
        answer, used_llm = ai_chat(
            question=body.question,
            db=db,
            profile=profile,
            conversation_history=body.conversation_history,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # LLM API errors — fall back to offline
        from ..services.chatbot import chatbot_answer
        answer, _ = chatbot_answer(body.question, db, profile)
        used_llm = False

    provider = settings.LLM_PROVIDER if used_llm else "offline"
    return AIChatResponse(answer=answer, used_llm=used_llm, provider=provider)


@router.post("/screen", response_model=EligibilityScreenResponse)
def screen(body: EligibilityScreenRequest, db: Session = Depends(get_db)):
    profile = _get_profile(db, body.profile_id)
    program = db.query(Program).filter(Program.program_key == body.program_key).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    try:
        screening, used_llm = screen_eligibility(
            program_key=body.program_key,
            db=db,
            profile=profile,
        )
    except Exception:
        from ..services.ranking import compute_rank
        score, why = compute_rank(program, profile)
        screening = f"Score: {score}/100\n" + "\n".join(f"- {w}" for w in why)
        used_llm = False

    return EligibilityScreenResponse(
        program_key=body.program_key,
        program_name=program.name,
        screening=screening,
        used_llm=used_llm,
    )
