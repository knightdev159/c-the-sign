"""Schemas for the assessment endpoint."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import CitationResponse, SafetyResponse


class AssessRequest(BaseModel):
    patient_id: str = Field(pattern=r"^PT-\d{3}$")
    top_k: int = Field(default=5, ge=1, le=20)


class AssessResponse(BaseModel):
    patient_id: str
    patient_name: str
    recommendation: Literal[
        "urgent_referral",
        "urgent_investigation",
        "no_urgent_action",
        "insufficient_evidence",
    ]
    reasoning: str
    matched_criteria: list[str]
    citations: list[CitationResponse]
    model: str
    grounded: bool
    safety: SafetyResponse
