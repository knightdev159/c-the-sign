"""Schemas for chat endpoints."""

from pydantic import BaseModel, Field

from app.schemas.common import CitationResponse, SafetyResponse


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[CitationResponse]
    grounded: bool
    safety: SafetyResponse


class ChatTurnResponse(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    history: list[ChatTurnResponse]


class ChatDeleteResponse(BaseModel):
    session_id: str
    deleted: bool
