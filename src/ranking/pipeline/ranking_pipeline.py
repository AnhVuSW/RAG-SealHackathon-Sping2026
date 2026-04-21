from typing import Optional
from ..config import RankingConfig
from ..reranker import CohereReranker, BGEReranker
from ..filter import Deduplicator, QualityFilter


class RankingPipeline:
    """Layer 3: Ranking & processing pipeline."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()
        self.cohere_reranker = CohereReranker()
        self.bge_reranker = BGEReranker()
        self.deduplicator = Deduplicator()
        self.quality_filter = QualityFilter(min_score=self.config.min_score)

    def process(self, query: str, documents: list[dict]) -> list[dict]:
        if not documents:
            return []

        reranked = self.bge_reranker.rerank(query, documents)
        deduplicated = self.deduplicator.deduplicate(reranked)
        filtered = self.quality_filter.filter(deduplicated)
        return filtered[: self.config.rerank_top_k]
