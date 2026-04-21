class ResponseSynthesizer:
    """LLM response generation."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def synthesize(self, query: str, context: str) -> str:
        # TODO: integrate LLM API
        if not context:
            return "No relevant documents found."
        return f"Based on the documents: {context[:200]}..."
