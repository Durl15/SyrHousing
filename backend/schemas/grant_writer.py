"""
Pydantic schemas for grant writer API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class GenerateRequest(BaseModel):
    application_id: str = Field(..., description="UUID of the application")
    content_type: str = Field(
        ...,
        description="Type of content to generate: cover_letter, eligibility_statement, project_description, needs_justification"
    )
    custom_prompt: Optional[str] = Field(None, description="Optional custom instructions for generation")


class GenerateResponse(BaseModel):
    content: str = Field(..., description="Generated content")
    used_llm: bool = Field(..., description="Whether LLM was used (true) or template fallback (false)")
    generated_at: datetime = Field(..., description="Timestamp of generation")
    version: int = Field(..., description="Version number of this draft")


class RefineRequest(BaseModel):
    application_id: str = Field(..., description="UUID of the application")
    content_type: str = Field(..., description="Type of content to refine")
    current_content: str = Field(..., description="Current content to be refined")
    feedback: str = Field(..., description="User feedback on what to improve")


class DraftResponse(BaseModel):
    drafts: Dict[str, Any] = Field(..., description="Dictionary of all saved drafts")

    class Config:
        json_schema_extra = {
            "example": {
                "drafts": {
                    "cover_letter": {
                        "content": "Dear Agency...",
                        "generated_at": "2024-01-15T10:30:00",
                        "version": 1,
                        "used_llm": True
                    },
                    "eligibility_statement": {
                        "content": "1. Location: I am a homeowner...",
                        "generated_at": "2024-01-15T10:35:00",
                        "version": 1,
                        "used_llm": True
                    }
                }
            }
        }
