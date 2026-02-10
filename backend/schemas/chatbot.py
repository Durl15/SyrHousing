from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str
    profile_id: Optional[str] = None


class MatchedProgram(BaseModel):
    program_key: str
    name: str
    match_score: int
    rank_score: int
    category: str
    program_type: Optional[str] = None
    max_benefit: Optional[str] = None
    status: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rank_explanation: List[str] = []


class ChatResponse(BaseModel):
    answer: str
    matched_programs: List[MatchedProgram]
