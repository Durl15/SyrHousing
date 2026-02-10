import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    program_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    menu_category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    repair_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_rank: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_benefit: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status_or_deadline: Mapped[str | None] = mapped_column(String(250), nullable=True)
    agency: Mapped[str | None] = mapped_column(String(250), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    eligibility_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    income_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    docs_checklist: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_programs_category_active", "menu_category", "is_active"),
    )
