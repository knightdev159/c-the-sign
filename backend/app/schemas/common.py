"""Shared API schemas."""

from typing import Literal

from pydantic import BaseModel


class CitationResponse(BaseModel):
    source: str
    page: int
    chunk_id: str
    excerpt: str


class SafetyResponse(BaseModel):
    action: Literal["allow", "qualify", "abstain"]
    groundedness_score: float
    evidence_coverage: float
    rule_consistency: Literal["pass", "fail", "unknown"]
    unsupported_claims: list[str]
    conflicts: list[str]
    notes: list[str]
