"""
Database models for Automated Grant Discovery system.
Tracks discovered grants through the admin review workflow.
"""

from sqlalchemy import String, Float, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from ..database import Base


class DiscoveredGrant(Base):
    """
    Tracks grants discovered from external sources pending admin review.

    Workflow: discovered → pending → approved/rejected/duplicate
    """
    __tablename__ = "discovered_grants"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Source metadata
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "rss_feed", "grants_gov_api", "web_scrape"
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(200), nullable=True)  # External ID (e.g., grants.gov opportunity ID)

    # Extracted grant data (mirrors Program model)
    name: Mapped[str] = mapped_column(String(250), nullable=False, index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    program_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    max_benefit: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status_or_deadline: Mapped[str | None] = mapped_column(String(250), nullable=True)
    agency: Mapped[str | None] = mapped_column(String(250), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    eligibility_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    docs_checklist: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Discovery metadata
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0.0-1.0
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob of original source data

    # Review workflow
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)  # "pending", "approved", "rejected", "duplicate"
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)  # Admin user ID
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Deduplication tracking
    matched_program_key: Mapped[str | None] = mapped_column(String(120), nullable=True)  # If duplicate detected
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # Fuzzy match score

    # Program creation tracking
    created_program_key: Mapped[str | None] = mapped_column(String(120), nullable=True)  # If converted to Program

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<DiscoveredGrant(id={self.id}, name={self.name}, source={self.source_type}, status={self.review_status})>"


class DiscoveryRun(Base):
    """
    Tracks execution of grant discovery runs.
    Stores statistics and error logs for monitoring and debugging.
    """
    __tablename__ = "discovery_runs"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Execution metadata
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")  # "running", "completed", "failed"

    # Statistics
    sources_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grants_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Error tracking
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of errors

    def __repr__(self):
        return f"<DiscoveryRun(id={self.id}, status={self.status}, discovered={self.grants_discovered}, duplicates={self.duplicates_found})>"
