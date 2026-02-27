"""Conversational agent over NG12 vector store."""

from __future__ import annotations

from app.schemas.chat import ChatResponse
from app.schemas.common import CitationResponse
from app.services.llm_client import LLMClient
from app.services.safety_validator import SafetyValidator
from app.services.vector_store import VectorStore
from app.storage.session_memory import ChatTurn, SessionMemoryStore


class ChatAgent:
    def __init__(
        self,
        memory_store: SessionMemoryStore,
        vector_store: VectorStore,
        llm_client: LLMClient,
        safety_validator: SafetyValidator,
    ) -> None:
        self._memory_store = memory_store
        self._vector_store = vector_store
        self._llm_client = llm_client
        self._safety_validator = safety_validator

    def respond(self, session_id: str, message: str, top_k: int = 5) -> ChatResponse:
        history = self._memory_store.get_history(session_id)
        # Keep only recent turns to avoid overly long prompts.
        recent_context = "\n".join(f"{turn.role}: {turn.content}" for turn in history[-6:])

        query = message if not recent_context else f"Context:\n{recent_context}\n\nQuestion:\n{message}"
        chunks = self._vector_store.query(query_text=query, top_k=top_k)

        citations = [
            CitationResponse(
                source=chunk.source,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                excerpt=chunk.excerpt,
            )
            for chunk in chunks[:3]
        ]

        if chunks:
            evidence_block = "\n".join(f"- [p.{chunk.page}] {chunk.document[:240]}" for chunk in chunks[: min(top_k, 5)])
            prompt = (
                f"Conversation context:\n{recent_context or '(none)'}\n\n"
                f"User question:\n{message}\n\n"
                f"Retrieved NG12 evidence:\n{evidence_block}\n\n"
                "Answer naturally using only the provided evidence."
            )
            answer = self._llm_client.generate(
                system_prompt=(
                    "You are an NG12 assistant. Do not invent unsupported clinical thresholds. "
                    "If evidence is weak, say so."
                ),
                user_prompt=prompt,
            )
        else:
            answer = "I couldn't find support in the NG12 text for that in the retrieved evidence."

        safety = self._safety_validator.validate(
            answer_text=answer,
            chunks=chunks,
            mode="chat",
        )
        grounded = bool(citations) and safety.action != "abstain"
        if safety.action == "abstain":
            # Replace the answer text when safety layer detects unsupported claims.
            answer = "I couldn't find sufficiently supported NG12 evidence to answer that safely."

        # Persist both user and assistant turns for follow-up questions.
        self._memory_store.append_turn(session_id, ChatTurn(role="user", content=message))
        self._memory_store.append_turn(session_id, ChatTurn(role="assistant", content=answer))

        return ChatResponse(
            session_id=session_id,
            answer=answer,
            citations=citations,
            grounded=grounded,
            safety=safety,
        )
