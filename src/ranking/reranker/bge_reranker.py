from .base_reranker import BaseReranker


class BGEReranker(BaseReranker):
    """BGE-Reranker local model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)

    def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        self._ensure_model()
        texts = [doc.get("text", "") for doc in documents]
        scores = self.model.predict([(query, text) for text in texts])
        scored = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored]
