class ContextCompactor:
    """Compress context to fit within token limit."""

    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens

    def compact(self, documents: list[dict], query: str) -> str:
        if not documents:
            return ""

        text_parts = []
        total_tokens = 0
        for doc in documents:
            text = doc.get("text", "")
            text_parts.append(text)
            total_tokens += len(text.split())

        combined = "\n\n".join(text_parts)
        if total_tokens > self.max_tokens:
            words = combined.split()
            combined = " ".join(words[: self.max_tokens])

        return combined
