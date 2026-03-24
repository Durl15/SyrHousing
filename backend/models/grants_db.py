"""
Grant-specific SQLAlchemy models.
Tables: grants, eligibility_criteria, grant_applications
"""
import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship

from ..database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Grant(Base):
    __tablename__ = "grants"

    id = Column(String(36), primary_key=True, default=_uuid)
    grant_name = Column(String(255), nullable=False, index=True)
    source = Column(String(255), nullable=True)
    amount_min = Column(Float, default=0.0)
    amount_max = Column(Float, nullable=True)
    # deadline: ISO date string "YYYY-MM-DD", "rolling", or "annual"
    deadline = Column(String(100), nullable=True)
    income_limit = Column(Float, nullable=True)      # Annual household income ceiling
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    # JSON arrays stored as text: ["single_family","multifamily",...]
    property_types = Column(Text, nullable=True)
    repair_categories = Column(Text, nullable=True)
    application_url = Column(String(500), nullable=True)
    # status: open | closing_soon | closed
    status = Column(String(20), nullable=False, default="open")
    last_verified = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    agency_phone = Column(String(50), nullable=True)
    agency_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    eligibility = relationship(
        "EligibilityCriteria",
        back_populates="grant",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "GrantApplication",
        back_populates="grant",
        cascade="all, delete-orphan",
    )

    def property_types_list(self) -> list:
        if not self.property_types:
            return []
        try:
            return json.loads(self.property_types)
        except (ValueError, TypeError):
            return []

    def repair_categories_list(self) -> list:
        if not self.repair_categories:
            return []
        try:
            return json.loads(self.repair_categories)
        except (ValueError, TypeError):
            return []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "grant_name": self.grant_name,
            "source": self.source,
            "amount_min": self.amount_min,
            "amount_max": self.amount_max,
            "deadline": self.deadline,
            "income_limit": self.income_limit,
            "age_min": self.age_min,
            "age_max": self.age_max,
            "property_types": self.property_types_list(),
            "repair_categories": self.repair_categories_list(),
            "application_url": self.application_url,
            "status": self.status,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "description": self.description,
            "agency_phone": self.agency_phone,
            "agency_email": self.agency_email,
        }


class EligibilityCriteria(Base):
    __tablename__ = "eligibility_criteria"

    id = Column(String(36), primary_key=True, default=_uuid)
    grant_id = Column(String(36), ForeignKey("grants.id", ondelete="CASCADE"), nullable=False, unique=True)
    requires_owner_occupied = Column(Boolean, default=True)
    requires_primary_residence = Column(Boolean, default=True)
    requires_us_citizen = Column(Boolean, default=False)
    geographic_restriction = Column(String(255), nullable=True)
    credit_score_min = Column(Integer, nullable=True)
    first_time_buyer_required = Column(Boolean, default=False)
    additional_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    grant = relationship("Grant", back_populates="eligibility")

    def to_dict(self) -> dict:
        return {
            "requires_owner_occupied": self.requires_owner_occupied,
            "requires_primary_residence": self.requires_primary_residence,
            "requires_us_citizen": self.requires_us_citizen,
            "geographic_restriction": self.geographic_restriction,
            "credit_score_min": self.credit_score_min,
            "first_time_buyer_required": self.first_time_buyer_required,
            "additional_notes": self.additional_notes,
        }


class GrantApplication(Base):
    __tablename__ = "grant_applications"

    id = Column(String(36), primary_key=True, default=_uuid)
    grant_id = Column(String(36), ForeignKey("grants.id", ondelete="CASCADE"), nullable=False)
    applicant_name = Column(String(255), nullable=True)
    applicant_email = Column(String(255), nullable=True)
    applicant_age = Column(Integer, nullable=True)
    applicant_income = Column(Float, nullable=True)
    property_type = Column(String(100), nullable=True)
    repair_category = Column(String(100), nullable=True)
    # status: draft | submitted | under_review | approved | rejected
    status = Column(String(50), nullable=False, default="draft")
    notes = Column(Text, nullable=True)
    documents_checklist = Column(Text, nullable=True)  # JSON array
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    grant = relationship("Grant", back_populates="applications")

    def to_dict(self) -> dict:
        checklist = []
        if self.documents_checklist:
            try:
                checklist = json.loads(self.documents_checklist)
            except (ValueError, TypeError):
                checklist = []
        return {
            "id": self.id,
            "grant_id": self.grant_id,
            "applicant_name": self.applicant_name,
            "applicant_email": self.applicant_email,
            "applicant_age": self.applicant_age,
            "applicant_income": self.applicant_income,
            "property_type": self.property_type,
            "repair_category": self.repair_category,
            "status": self.status,
            "notes": self.notes,
            "documents_checklist": checklist,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
