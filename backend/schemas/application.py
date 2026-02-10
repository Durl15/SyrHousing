from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ApplicationCreate(BaseModel):
    program_key: str
    notes: str = ""


class ApplicationUpdate(BaseModel):
    notes: Optional[str] = None
    documents_checklist: Optional[dict] = None


class ApplicationStatusChange(BaseModel):
    status: str
    notes: Optional[str] = None


class StatusHistoryRead(BaseModel):
    id: str
    from_status: Optional[str]
    to_status: str
    notes: Optional[str]
    changed_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationRead(BaseModel):
    id: str
    user_id: str
    program_key: str
    program_name: str = ""
    status: str
    notes: Optional[str]
    documents_checklist: Optional[dict]
    created_at: datetime
    updated_at: datetime
    applied_at: Optional[datetime]
    decided_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ApplicationDetail(ApplicationRead):
    status_history: List[StatusHistoryRead] = []
