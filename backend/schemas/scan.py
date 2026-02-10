from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScanResultRead(BaseModel):
    id: str
    timestamp: datetime
    watchlist_program_key: str
    name: str
    url: str
    status: str
    changed: bool
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ScanStateRead(BaseModel):
    program_key: str
    name: str
    url: str
    status: str
    content_hash: Optional[str] = None
    last_checked: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ScanTriggerResponse(BaseModel):
    message: str
    scanned: int
    changes: int
    errors: int
    results: List[ScanResultRead]
