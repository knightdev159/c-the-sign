"""Chat endpoints."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_chat_agent, get_memory_store
from app.schemas.chat import (
    ChatDeleteResponse,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatTurnResponse,
)
from app.services.chat_agent import ChatAgent
from app.storage.session_memory import SessionMemoryStore

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, agent: ChatAgent = Depends(get_chat_agent)) -> ChatResponse:
    return agent.respond(session_id=payload.session_id, message=payload.message, top_k=payload.top_k)


@router.get("/chat/{session_id}/history", response_model=ChatHistoryResponse)
def chat_history(
    session_id: str,
    memory_store: SessionMemoryStore = Depends(get_memory_store),
) -> ChatHistoryResponse:
    history = [ChatTurnResponse(role=turn.role, content=turn.content) for turn in memory_store.get_history(session_id)]
    return ChatHistoryResponse(session_id=session_id, history=history)


@router.delete("/chat/{session_id}", response_model=ChatDeleteResponse)
def chat_delete(
    session_id: str,
    memory_store: SessionMemoryStore = Depends(get_memory_store),
) -> ChatDeleteResponse:
    deleted = memory_store.clear(session_id)
    return ChatDeleteResponse(session_id=session_id, deleted=deleted)
