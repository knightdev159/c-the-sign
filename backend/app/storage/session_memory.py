"""In-memory chat session store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class ChatTurn:
    role: str
    content: str


@dataclass
class SessionState:
    turns: list[ChatTurn]
    updated_at: datetime


class SessionMemoryStore:
    """Simple in-memory session memory with TTL and turn limit."""

    def __init__(self, max_turns: int = 20, ttl_hours: int = 24) -> None:
        self._max_turns = max_turns
        self._ttl = timedelta(hours=ttl_hours)
        self._sessions: dict[str, SessionState] = {}

    def append_turn(self, session_id: str, turn: ChatTurn) -> None:
        self._cleanup_expired()
        now = datetime.now(tz=UTC)
        state = self._sessions.get(session_id)
        if state is None:
            state = SessionState(turns=[], updated_at=now)
            self._sessions[session_id] = state

        state.turns.append(turn)
        if len(state.turns) > self._max_turns:
            state.turns = state.turns[-self._max_turns :]
        state.updated_at = now

    def get_history(self, session_id: str) -> list[ChatTurn]:
        self._cleanup_expired()
        state = self._sessions.get(session_id)
        return list(state.turns) if state else []

    def clear(self, session_id: str) -> bool:
        self._cleanup_expired()
        return self._sessions.pop(session_id, None) is not None

    def _cleanup_expired(self) -> None:
        now = datetime.now(tz=UTC)
        expired = [sid for sid, state in self._sessions.items() if now - state.updated_at > self._ttl]
        for sid in expired:
            self._sessions.pop(sid, None)
