from typing import Any


class SessionMemory:
    """Short-term session memory store."""

    def __init__(self):
        self.sessions: dict[str, list[dict]] = {}

    def add(self, session_id: str, entry: dict):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(entry)

    def get(self, session_id: str) -> list[dict]:
        return self.sessions.get(session_id, [])

    def clear(self, session_id: str):
        self.sessions[session_id] = []
