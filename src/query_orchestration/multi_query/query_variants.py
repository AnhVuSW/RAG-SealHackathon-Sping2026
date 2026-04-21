class QueryVariantGenerator:
    """Generate query variants for multi-query retrieval."""

    def __init__(self, count: int = 5, prompt_template: str = None):
        self.count = count
        self.prompt_template = prompt_template or (
            "Generate {count} different versions of the given question to retrieve "
            "relevant documents from a vector database.\nOriginal question: {query}\n"
            "Generate {count} alternative questions:"
        )

    def generate(self, query: str) -> list[str]:
        prompt = self.prompt_template.format(count=self.count, query=query)
        # TODO: integrate LLM for actual generation
        return [query]
