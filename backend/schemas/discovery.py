"""
Pydantic schemas for grant discovery API endpoints.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DiscoveredGrantRead(BaseModel):
    """Response model for discovered grants."""
    id: str
    source_type: str
    source_url: str
    source_id: Optional[str] = None
    name: str
    jurisdiction: Optional[str] = None
    program_type: Optional[str] = None
    max_benefit: Optional[str] = None
    status_or_deadline: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    eligibility_summary: Optional[str] = None
    docs_checklist: Optional[str] = None
    discovered_at: datetime
    confidence_score: float
    review_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    matched_program_key: Optional[str] = None
    similarity_score: Optional[float] = None
    created_program_key: Optional[str] = None

    class Config:
        from_attributes = True


class DiscoveryRunRead(BaseModel):
    """Response model for discovery runs."""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    sources_checked: int
    grants_discovered: int
    duplicates_found: int
    errors: int

    class Config:
        from_attributes = True


class DiscoveryRunDetail(DiscoveryRunRead):
    """Detailed discovery run with error log."""
    error_log: str  # JSON string


class TriggerDiscoveryRequest(BaseModel):
    """Request to trigger manual discovery."""
    sources: Optional[list[str]] = Field(
        None,
        description="List of sources to check (None = all sources)",
        examples=[["rss_feed"], ["rss_feed", "grants_gov_api"]]
    )
    send_notification: bool = Field(
        True,
        description="Whether to send admin notification email"
    )


class ApproveGrantRequest(BaseModel):
    """Request to approve a discovered grant."""
    create_program: bool = Field(
        True,
        description="Whether to create a Program record"
    )
    program_key: Optional[str] = Field(
        None,
        description="Custom program_key (auto-generated if None)"
    )
    # Optional overrides for Program creation
    name: Optional[str] = None
    jurisdiction: Optional[str] = None
    program_type: Optional[str] = None
    max_benefit: Optional[str] = None
    status_or_deadline: Optional[str] = None
    agency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    eligibility_summary: Optional[str] = None
    docs_checklist: Optional[str] = None
    menu_category: Optional[str] = None
    priority_rank: Optional[float] = Field(None, ge=0.0, le=100.0)


class RejectGrantRequest(BaseModel):
    """Request to reject a discovered grant."""
    reason: str = Field(
        ...,
        description="Reason for rejection",
        min_length=1,
        max_length=500
    )


class MarkDuplicateRequest(BaseModel):
    """Request to mark a grant as duplicate."""
    program_key: str = Field(
        ...,
        description="Program key of the duplicate program"
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes about the duplicate match",
        max_length=500
    )


class DiscoveryStats(BaseModel):
    """Summary statistics for discovery system."""
    total_runs: int
    total_discovered: int
    total_duplicates: int
    pending_review: int
    approved: int
    rejected: int
    avg_confidence: float
    last_run_at: Optional[datetime] = None
