from typing import Optional, Tuple
from ..config import SynthesisConfig
from ..compact import ContextCompactor
from ..memory import SessionMemory, AutoDream
from ..llm import ResponseSynthesizer


class SynthesisPipeline:
    """Layer 4: Synthesis & memory pipeline."""

    def __init__(self, config: Optional[SynthesisConfig] = None):
        self.config = config or SynthesisConfig()
        self.compactor = ContextCompactor(max_tokens=self.config.compact_max_tokens)
        self.memory = SessionMemory()
        self.auto_dream = AutoDream(interval_minutes=self.config.dream_interval_minutes)
        self.synthesizer = ResponseSynthesizer(model=self.config.llm_model)

    def synthesize(
        self, query: str, documents: list[dict]
    ) -> Tuple[str, dict]:
        context = self.compactor.compact(documents, query)
        response = self.synthesizer.synthesize(query, context)
        metadata = {"session_id": "default", "docs_used": len(documents)}
        return response, metadata

    async def process(
        self, query: str, documents: list[dict], session_id: str = "default"
    ) -> Tuple[str, dict]:
        context = self.compactor.compact(documents, query)
        response = self.synthesizer.synthesize(query, context)

        self.memory.add(session_id, {"query": query, "response": response})

        if self.auto_dream.should_run():
            await self.auto_dream.dream(session_id)

        metadata = {"session_id": session_id, "docs_used": len(documents)}
        return response, metadata
