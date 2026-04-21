from .base_reranker import BaseReranker


class CohereReranker(BaseReranker):
    """Cohere API reranker."""

    def __init__(self, api_key: str = None, model: str = "rerank-multilingual-v3.0"):
        self.api_key = api_key
        self.model = model

    def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        # TODO: integrate Cohere API
        return documents
