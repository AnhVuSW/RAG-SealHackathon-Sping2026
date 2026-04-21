class HyDETransform:
    """HyDE (Hypothetical Document Embeddings) transformation."""

    def __init__(self, prompt_template: str = None):
        self.prompt_template = prompt_template or (
            "Write a passage that would answer the question: {query}"
        )

    def transform(self, query: str) -> str:
        prompt = self.prompt_template.format(query=query)
        # TODO: integrate LLM to generate hypothetical document
        return query
