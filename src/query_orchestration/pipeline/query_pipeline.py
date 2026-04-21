from typing import Optional
from ..config import QueryOrchestrationConfig
from ..multi_query import QueryVariantGenerator
from ..transformation import HyDETransform
from ..fusion import ReciprocalRankFusion


class QueryPipeline:
    """Layer 2: Query orchestration pipeline."""

    def __init__(self, config: Optional[QueryOrchestrationConfig] = None):
        self.config = config or QueryOrchestrationConfig()
        self.variant_generator = QueryVariantGenerator(
            count=self.config.multi_query_count,
            prompt_template=self.config.multi_query_prompt,
        )
        self.hyde = HyDETransform(prompt_template=self.config.hyde_prompt) if self.config.hyde_enabled else None
        self.fusion = ReciprocalRankFusion()

    def process(self, query: str) -> list[dict]:
        queries = self.variant_generator.generate(query)
        if self.hyde:
            hypothetical = self.hyde.transform(query)
            queries.append(hypothetical)

        results = []
        for q in queries:
            doc_results = self._search(q)
            results.append(doc_results)

        fused = self.fusion.fuse(results) if len(results) > 1 else results[0] if results else []
        return fused[: self.config.top_k]

    def _search(self, query: str) -> list[dict]:
        # TODO: integrate LanceDB reader for actual vector search
        return []

    async def aprocess(self, query: str) -> list[dict]:
        return self.process(query)
