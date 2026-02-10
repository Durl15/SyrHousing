from pydantic import BaseModel
from typing import Optional, List, Dict


class AIChatRequest(BaseModel):
    question: str
    profile_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class AIChatResponse(BaseModel):
    answer: str
    used_llm: bool
    provider: str


class EligibilityScreenRequest(BaseModel):
    program_key: str
    profile_id: Optional[str] = None


class EligibilityScreenResponse(BaseModel):
    program_key: str
    program_name: str
    screening: str
    used_llm: bool


class AIStatusResponse(BaseModel):
    llm_available: bool
    provider: str
    model: str
