from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_applications: int
    applications_by_status: Dict[str, int]
    active_programs: int
    recent_registrations: int


class UserAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[str] = None


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    application_count: int = 0

    model_config = {"from_attributes": True}
