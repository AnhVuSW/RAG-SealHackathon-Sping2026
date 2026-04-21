import asyncio
from datetime import datetime


class AutoDream:
    """Background dreaming process for long-term memory consolidation."""

    def __init__(self, interval_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self.last_dream = datetime.now()

    async def dream(self, session_id: str):
        """Process session memory for long-term consolidation."""
        await asyncio.sleep(0)
        self.last_dream = datetime.now()

    def should_run(self) -> bool:
        elapsed = (datetime.now() - self.last_dream).total_seconds() / 60
        return elapsed >= self.interval_minutes
