from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProgramCreate(BaseModel):
    program_key: str = Field(..., max_length=120)
    name: str = Field(..., max_length=250)
    jurisdiction: Optional[str] = None
    program_type: Optional[str] = None
    menu_category: str = Field(..., max_length=60)
    repair_tags: Optional[str] = None
    priority_rank: float = 0.0
    max_benefit: Optional[str] = None
    status_or_deadline: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    eligibility_summary: Optional[str] = None
    income_guidance: Optional[str] = None
    docs_checklist: Optional[str] = None


class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    jurisdiction: Optional[str] = None
    program_type: Optional[str] = None
    menu_category: Optional[str] = None
    repair_tags: Optional[str] = None
    priority_rank: Optional[float] = None
    max_benefit: Optional[str] = None
    status_or_deadline: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    eligibility_summary: Optional[str] = None
    income_guidance: Optional[str] = None
    docs_checklist: Optional[str] = None
    is_active: Optional[bool] = None


class ProgramRead(BaseModel):
    id: str
    program_key: str
    name: str
    jurisdiction: Optional[str] = None
    program_type: Optional[str] = None
    menu_category: str
    repair_tags: Optional[str] = None
    priority_rank: float
    max_benefit: Optional[str] = None
    status_or_deadline: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    eligibility_summary: Optional[str] = None
    income_guidance: Optional[str] = None
    docs_checklist: Optional[str] = None
    last_verified: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class ProgramWithRank(ProgramRead):
    computed_score: int = 0
    rank_explanation: List[str] = []
