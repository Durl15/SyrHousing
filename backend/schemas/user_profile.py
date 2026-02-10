from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ProfileCreate(BaseModel):
    profile_name: str = Field(default="default", max_length=100)
    city: str = Field(default="Syracuse", max_length=100)
    county: str = Field(default="Onondaga", max_length=100)
    is_senior: bool = True
    is_fixed_income: bool = True
    repair_needs: Optional[List[str]] = None
    repair_severity: Optional[Dict[str, int]] = None


class ProfileUpdate(BaseModel):
    profile_name: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    is_senior: Optional[bool] = None
    is_fixed_income: Optional[bool] = None
    repair_needs: Optional[List[str]] = None
    repair_severity: Optional[Dict[str, int]] = None


class ProfileRead(BaseModel):
    id: str
    user_id: Optional[str] = None
    profile_name: str
    city: str
    county: str
    is_senior: bool
    is_fixed_income: bool
    repair_needs: Optional[List[str]] = None
    repair_severity: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
