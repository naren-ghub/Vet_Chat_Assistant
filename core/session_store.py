from __future__ import annotations

import time
from typing import Dict, Tuple

from core.types import SessionState


class SessionStore:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._ttl = ttl_seconds
        self._sessions: Dict[str, Tuple[float, SessionState]] = {}

    def get(self, session_id: str) -> SessionState:
        self._cleanup()
        entry = self._sessions.get(session_id)
        if entry:
            _, session = entry
            self._sessions[session_id] = (time.time(), session)
            return session
        session = SessionState(session_id=session_id)
        self._sessions[session_id] = (time.time(), session)
        return session

    def update_location(self, session_id: str, location: str) -> None:
        session = self.get(session_id)
        session.pet_profile["location"] = location
        self._sessions[session_id] = (time.time(), session)

    def _cleanup(self) -> None:
        now = time.time()
        expired = [sid for sid, (ts, _) in self._sessions.items() if now - ts > self._ttl]
        for sid in expired:
            self._sessions.pop(sid, None)
