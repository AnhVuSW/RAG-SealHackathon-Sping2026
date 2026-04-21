from dataclasses import dataclass


@dataclass
class QueryOrchestrationConfig:
    multi_query_count: int = 5
    multi_query_prompt: str = "Generate {count} different versions of the given question to retrieve relevant documents."
    hyde_enabled: bool = True
    hyde_prompt: str = "Write a passage that would answer the question: {query}"
    top_k: int = 20
