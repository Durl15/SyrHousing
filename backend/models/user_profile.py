import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False, default="default", index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Syracuse")
    county: Mapped[str] = mapped_column(String(100), nullable=False, default="Onondaga")
    is_senior: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_fixed_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    repair_needs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    repair_severity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
