from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user_profile import UserProfile
from ..schemas.chatbot import ChatRequest, ChatResponse, MatchedProgram
from ..services.chatbot import chatbot_answer

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


@router.post("/ask", response_model=ChatResponse)
def ask(body: ChatRequest, db: Session = Depends(get_db)):
    if body.profile_id:
        profile = db.query(UserProfile).filter(UserProfile.id == body.profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
    else:
        profile = db.query(UserProfile).filter(UserProfile.profile_name == "default").first()
        if not profile:
            raise HTTPException(status_code=404, detail="No default profile found")

    answer, matched = chatbot_answer(body.question, db, profile)

    return ChatResponse(
        answer=answer,
        matched_programs=[MatchedProgram(**m) for m in matched],
    )
