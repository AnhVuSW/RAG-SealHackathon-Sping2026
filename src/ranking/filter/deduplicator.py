class Deduplicator:
    """Remove duplicate content from results."""

    def deduplicate(self, documents: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for doc in documents:
            text = doc.get("text", "")
            if text not in seen:
                seen.add(text)
                unique.append(doc)
        return unique
