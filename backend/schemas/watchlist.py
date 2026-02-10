from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WatchlistCreate(BaseModel):
    program_key: str = Field(..., max_length=120)
    name: str = Field(..., max_length=250)
    url: str = Field(..., max_length=500)
    open_keywords: Optional[str] = None
    closed_keywords: Optional[str] = None
    notes: Optional[str] = None


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    open_keywords: Optional[str] = None
    closed_keywords: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class WatchlistRead(BaseModel):
    id: str
    program_key: str
    name: str
    url: str
    open_keywords: Optional[str] = None
    closed_keywords: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
