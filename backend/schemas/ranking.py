from pydantic import BaseModel
from typing import Optional, List


class RankRequest(BaseModel):
    profile_id: Optional[str] = None
    program_keys: Optional[List[str]] = None


class RankResult(BaseModel):
    program_key: str
    name: str
    menu_category: str
    computed_score: int
    explanation: List[str]


class RankResponse(BaseModel):
    profile_id: str
    results: List[RankResult]
