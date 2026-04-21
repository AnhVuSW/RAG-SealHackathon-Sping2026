from dataclasses import dataclass


@dataclass
class RankingConfig:
    reranker_model: str = "BAAI/bge-reranker-base"
    top_k: int = 20
    rerank_top_k: int = 5
    min_score: float = 0.0
