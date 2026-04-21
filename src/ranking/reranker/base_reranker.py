from abc import ABC, abstractmethod


class BaseReranker(ABC):
    """Abstract base class for reranker models."""

    @abstractmethod
    def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        pass
