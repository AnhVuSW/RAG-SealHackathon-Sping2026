class QualityFilter:
    """Filter low-quality results."""

    def __init__(self, min_score: float = 0.0):
        self.min_score = min_score

    def filter(self, documents: list[dict]) -> list[dict]:
        return [doc for doc in documents if doc.get("score", 1.0) >= self.min_score]
