from typing import Sequence


class ReciprocalRankFusion:
    """Reciprocal Rank Fusion for combining multiple query results."""

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        result_lists: Sequence[Sequence[dict]],
    ) -> list[dict]:
        """Fuse multiple ranked result lists using RRF."""
        scores = {}
        for result_list in result_lists:
            for rank, doc in enumerate(result_list):
                doc_id = doc.get("id", doc.get("text", ""))
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.k + rank + 1)

        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc for doc_id, _ in fused for result_list in result_lists for doc in result_list if doc.get("id", doc.get("text", "")) == doc_id]
