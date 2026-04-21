# Layer 2: Query Orchestration

## Overview

| Property | Value |
|----------|-------|
| Layer | 2 |
| Keyword | RETRIEVAL OPTIMIZATION |
| Components | Multi-Query + HyDE + Query Transformation |
| Purpose | Transform and expand user queries for better retrieval |
| Status | **Standalone** - Can run independently |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  QUERY ORCHESTRATION PIPELINE                │
└──────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │   User Query    │
                         │  "What is AI?"  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌──────────────────┐       ┌──────────────────┐
         │   Multi-Query     │       │      HyDE        │
         │  (Query Variants) │       │ (Hypothetical   │
         │                   │       │  Documents)      │
         └────────┬─────────┘       └────────┬─────────┘
                  │                          │
                  │   ┌──────────────────────┘
                  │   │
                  ▼   ▼
         ┌──────────────────┐
         │  Query Fusion    │
         │  (Combine All)   │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  LanceDB Search  │
         │  (Parallel)     │
         └──────────────────┘
```

## File Structure

```
layer2_query_orchestration/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration
├── multi_query/
│   ├── __init__.py
│   └── query_variants.py      # Generate query variants
├── transformation/
│   ├── __init__.py
│   └── hyde_transform.py      # HyDE transformation
├── fusion/
│   ├── __init__.py
│   └── reciprocal_rank.py    # RRF fusion
└── pipeline/
    ├── __init__.py
    └── query_pipeline.py       # Orchestration pipeline
```

## Installation

```bash
pip install llama-index llama-index-llms-openai \
    openai sentence-transformers
```

## Configuration

```python
# layer2_query_orchestration/config.py
from dataclasses import dataclass

@dataclass
class QueryOrchestrationConfig:
    # Multi-Query
    multi_query_count: int = 5
    multi_query_prompt: str = """Generate {count} different versions of the given question
to retrieve relevant documents from a vector database.
The goal is to help find documents that might have different wording
or aspects of the same topic.

Original question: {query}

Generate {count} alternative questions:"""

    # HyDE
    hyde_enabled: bool = True
    hyde_prompt: str = """Write a passage that would answer the question:
{query}

Passage:"""
    hyde_model: str = "gpt-4o"

    # Fusion
    fusion_method: str = "rrf"  # Reciprocal Rank Fusion
    rrf_k: int = 60

    # Retrieval
    vector_top_k: int = 20
    rerank_top_k: int = 5
```

## Multi-Query Strategy

### Concept

Instead of searching with just the original query, generate multiple query variants to maximize recall.

```python
# layer2_query_orchestration/multi_query/query_variants.py
from typing import list

class MultiQueryGenerator:
    """Generate multiple variants of a query."""

    def __init__(self, llm, config: QueryOrchestrationConfig):
        self.llm = llm
        self.config = config

    def generate(self, query: str) -> list[str]:
        """Generate query variants."""
        prompt = self.config.multi_query_prompt.format(
            count=self.config.multi_query_count,
            query=query
        )

        response = self.llm.complete(prompt)
        variants = [query] + self._parse_variants(response.text)

        return variants[:self.config.multi_query_count]

    def _parse_variants(self, text: str) -> list[str]:
        """Parse variants from LLM response."""
        lines = text.strip().split("\n")
        variants = []
        for line in lines:
            # Remove numbering (1., 2., etc.)
            cleaned = line.lstrip("0123456789. )-")
            if cleaned.strip():
                variants.append(cleaned.strip())
        return variants
```

### Example

```
Original: "What is machine learning?"

Variants:
1. "Define machine learning and its applications"
2. "How does machine learning work?"
3. "Machine learning algorithms and techniques"
4. "Difference between ML and deep learning"
5. "Real-world uses of machine learning"
```

## HyDE (Hypothetical Document Embeddings)

### Concept

Generate a hypothetical document that would answer the query, then use that document's embedding for retrieval.

```python
# layer2_query_orchestration/transformation/hyde_transform.py
from typing import Optional

class HyDETransformer:
    """Transform query using HyDE technique."""

    def __init__(self, llm, embed_model, config: QueryOrchestrationConfig):
        self.llm = llm
        self.embed_model = embed_model
        self.config = config

    def transform(self, query: str) -> tuple[str, list[float]]:
        """
        Transform query using HyDE.
        Returns: (hypothetical_document, embedding)
        """
        # Generate hypothetical document
        prompt = self.config.hyde_prompt.format(query=query)
        hypothetical_doc = self.llm.complete(prompt).text

        # Embed the hypothetical document
        embedding = self.embed_model.embed([hypothetical_doc])[0]

        return hypothetical_doc, embedding

    async def atransform(self, query: str) -> tuple[str, list[float]]:
        """Async version for better performance."""
        prompt = self.config.hyde_prompt.format(query=query)
        response = await self.llm.acomplete(prompt)
        hypothetical_doc = response.text
        embedding = self.embed_model.embed([hypothetical_doc])[0]
        return hypothetical_doc, embedding
```

### Example

```
Original Query: "What is RAG in LLM?"

Hypothetical Document:
"RAG (Retrieval-Augmented Generation) is a technique that combines
retrieval systems with LLMs. It works by first retrieving relevant
documents from a knowledge base, then using those documents as
context to generate more accurate responses. RAG helps reduce
hallucinations and provides up-to-date information."

Embedding: [0.123, -0.456, ...]  # Based on the hypothetical doc
```

## Query Fusion (RRF)

### Reciprocal Rank Fusion

Combine results from multiple queries using Reciprocal Rank Fusion.

```python
# layer2_query_orchestration/fusion/reciprocal_rank.py
from typing import Dict, List

def reciprocal_rank_fusion(
    results_by_query: Dict[str, List[dict]],
    k: int = 60
) -> List[dict]:
    """
    Fuse results from multiple queries using RRF.

    RRF Score = Σ 1/(k + rank)
    where rank starts at 1
    """
    doc_scores: Dict[str, float] = {}

    for query, results in results_by_query.items():
        for rank, doc in enumerate(results, start=1):
            doc_id = doc["id"]
            score = 1 / (k + rank)

            if doc_id in doc_scores:
                doc_scores[doc_id] += score
            else:
                doc_scores[doc_id] = score
                doc_scores[f"{doc_id}_data"] = doc

    # Sort by score descending
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1] if isinstance(x[1], float) else 0,
        reverse=True
    )

    # Return deduplicated results
    seen = set()
    fused_results = []
    for doc_id, score in sorted_docs:
        if doc_id.endswith("_data"):
            continue
        if doc_id not in seen:
            doc_data = doc_scores.get(f"{doc_id}_data", {})
            doc_data["fusion_score"] = score
            fused_results.append(doc_data)
            seen.add(doc_id)

    return fused_results
```

## Query Pipeline

```python
# layer2_query_orchestration/pipeline/query_pipeline.py
from typing import Optional
from ..multi_query.query_variants import MultiQueryGenerator
from ..transformation.hyde_transform import HyDETransformer
from ..fusion.reciprocal_rank import reciprocal_rank_fusion

class QueryPipeline:
    """Main orchestration pipeline for query processing."""

    def __init__(self, llm, embed_model, vector_store, config):
        self.llm = llm
        self.embed_model = embed_model
        self.vector_store = vector_store
        self.config = config

        self.multi_query = MultiQueryGenerator(llm, config)
        self.hyde = HyDETransformer(llm, embed_model, config)

    def process(self, query: str) -> list[dict]:
        """
        Process query through full pipeline:
        1. Multi-Query generation
        2. HyDE transformation
        3. Parallel vector search
        4. RRF fusion
        """
        all_results = {}

        # 1. Original query search
        original_embedding = self.embed_model.embed([query])[0]
        original_results = self.vector_store.search(
            original_embedding,
            top_k=self.config.vector_top_k
        )
        all_results["original"] = original_results

        # 2. Multi-Query variants
        if self.config.multi_query_count > 0:
            variants = self.multi_query.generate(query)
            for i, variant in enumerate(variants[1:], start=1):  # Skip original
                variant_embedding = self.embed_model.embed([variant])[0]
                variant_results = self.vector_store.search(
                    variant_embedding,
                    top_k=self.config.vector_top_k
                )
                all_results[f"variant_{i}"] = variant_results

        # 3. HyDE transformation
        if self.config.hyde_enabled:
            hypothetical_doc, hyde_embedding = self.hyde.transform(query)
            hyde_results = self.vector_store.search(
                hyde_embedding,
                top_k=self.config.vector_top_k
            )
            all_results["hyde"] = hyde_results

        # 4. Fusion
        fused_results = reciprocal_rank_fusion(
            all_results,
            k=self.config.rrf_k
        )

        return fused_results[:self.config.rerank_top_k]

    async def aprocess(self, query: str) -> list[dict]:
        """Async version for better performance."""
        all_results = {}

        # Parallel embedding generation
        original_embedding = self.embed_model.embed([query])[0]
        original_results = self.vector_store.search(original_embedding, top_k=self.config.vector_top_k)
        all_results["original"] = original_results

        # Multi-Query
        variants = self.multi_query.generate(query)
        hyde_task = None

        if self.config.multi_query_count > 0:
            for i, variant in enumerate(variants[1:], start=1):
                variant_embedding = self.embed_model.embed([variant])[0]
                variant_results = self.vector_store.search(variant_embedding, top_k=self.config.vector_top_k)
                all_results[f"variant_{i}"] = variant_results

        # HyDE (parallel)
        if self.config.hyde_enabled:
            hypothetical_doc, hyde_embedding = await self.hyde.atransform(query)
            hyde_results = self.vector_store.search(hyde_embedding, top_k=self.config.vector_top_k)
            all_results["hyde"] = hyde_results

        # Fusion
        fused_results = reciprocal_rank_fusion(all_results, k=self.config.rrf_k)
        return fused_results[:self.config.rerank_top_k]
```

## Main Entry Point

```python
# layer2_query_orchestration/main.py
import argparse
import asyncio
from .config import QueryOrchestrationConfig
from .pipeline.query_pipeline import QueryPipeline

# Mock vector store for standalone testing
class MockVectorStore:
    def __init__(self):
        self.data = [
            {"id": "1", "text": "Machine learning is a subset of AI"},
            {"id": "2", "text": "Deep learning uses neural networks"},
            {"id": "3", "text": "Python is popular for ML"},
        ]

    def search(self, embedding: list[float], top_k: int) -> list[dict]:
        return self.data[:top_k]

def main():
    parser = argparse.ArgumentParser(description="Layer 2: Query Orchestration")
    parser.add_argument("--query", type=str, required=True, help="Query to process")
    parser.add_argument("--test-mode", action="store_true", help="Use mock data")
    args = parser.parse_args()

    if args.test_mode:
        # Test with mock data
        config = QueryOrchestrationConfig()
        pipeline = QueryPipeline(
            llm=None,  # Won't use for HyDE in test mode
            embed_model=None,  # Mock embedding
            vector_store=MockVectorStore(),
            config=config
        )
        results = pipeline.process(args.query)
        print(f"Query: {args.query}")
        print(f"Results: {results}")
    else:
        print("Full pipeline requires LLM and vector store connections")

if __name__ == "__main__":
    main()
```

## Testing

```bash
# Test Multi-Query only
python -c "
from layer2_query_orchestration.multi_query import MultiQueryGenerator

# Mock LLM
class MockLLM:
    def complete(self, prompt):
        class Response:
            text = '''1. Define machine learning
2. How does ML work?
3. ML algorithms explained'''
        return Response()

config = QueryOrchestrationConfig(multi_query_count=3)
generator = MultiQueryGenerator(MockLLM(), config)
variants = generator.generate('What is machine learning?')
print(f'Generated {len(variants)} variants')
for v in variants:
    print(f'  - {v}')
"

# Test RRF fusion
python -c "
from layer2_query_orchestration.fusion import reciprocal_rank_fusion

results = {
    'q1': [{'id': '1'}, {'id': '2'}, {'id': '3'}],
    'q2': [{'id': '2'}, {'id': '3'}, {'id': '4'}],
    'q3': [{'id': '3'}, {'id': '4'}, {'id': '5'}],
}

fused = reciprocal_rank_fusion(results, k=60)
print('Fused results:', [r['id'] for r in fused])
"
```

## Layer Communication

Layer 2 receives query from user, outputs ranked document IDs to Layer 3.

```python
# Interface between Layer 2 and Layer 3
@dataclass
class QueryResult:
    query: str
    documents: List[dict]  # [{id, text, score, fusion_score}]
    metadata: dict  # timing, query_variants used, etc.

# Layer 3 receives QueryResult
def layer3_process(layer2_output: QueryResult):
    for doc in layer2_output.documents:
        # Apply reranking
        pass
```

## Performance Considerations

| Technique | Latency Impact | Recall Improvement |
|-----------|---------------|-------------------|
| Multi-Query (3 variants) | +200-500ms | +20-40% |
| Multi-Query (5 variants) | +400-800ms | +30-50% |
| HyDE | +300-600ms | +15-30% |
| Combined (Multi + HyDE) | +600-1000ms | +40-60% |

### Latency Mitigation

```python
# Use async for parallel execution
async def process_with_latency_masking(self, query: str):
    # Start all operations concurrently
    multi_task = asyncio.create_task(self.multi_query.agenerate(query))
    hyde_task = asyncio.create_task(self.hyde.atransform(query))
    embed_task = asyncio.create_task(self.embed_model.aembed([query]))

    # Await all - total time = max(all_times), not sum
    variants = await multi_task
    hyde_doc, hyde_emb = await hyde_task
    original_emb = await embed_task
```

---

**Previous**: [Layer 1: Ingestion](./layer-1-ingestion.md)
**Next**: [Layer 3: Ranking & Processing](./layer-3-ranking-processing.md)
