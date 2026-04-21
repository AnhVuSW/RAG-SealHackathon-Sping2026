# Layer 3: Ranking & Processing

## Overview

| Property | Value |
|----------|-------|
| Layer | 3 |
| Keyword | POST-PROCESSING |
| Components | LlamaIndex Reranker (Cohere/BGE-Reranker) |
| Purpose | Rerank retrieved documents, filter low-quality results |
| Status | **Standalone** - Can run independently |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   RANKING & PROCESSING PIPELINE              │
└──────────────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────┐
         │           Layer 2 Output               │
         │   (Top-20 Documents from RRF)          │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │            Reranker Model               │
         │   ┌─────────────┬─────────────────┐    │
         │   │   Cohere    │   BGE-Reranker  │    │
         │   │  (API)      │   (Local)       │    │
         │   └─────────────┴─────────────────┘    │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │        Relevance Scoring               │
         │    Query-Doc Similarity Scores         │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │        Quality Filter                  │
         │   ┌─────────────────────────────────┐  │
         │   │  - Remove duplicates            │  │
         │   │  - Filter low scores            │  │
         │   │  - Deduplicate by content        │  │
         │   └─────────────────────────────────┘  │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │         Layer 4 Output                 │
         │   (Top-5 Reranked Documents)          │
         └─────────────────────────────────────────┘
```

## File Structure

```
layer3_ranking/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration
├── reranker/
│   ├── __init__.py
│   ├── base_reranker.py       # Abstract base
│   ├── cohere_reranker.py     # Cohere API reranker
│   └── bge_reranker.py        # BGE-Reranker local
├── filter/
│   ├── __init__.py
│   ├── deduplicator.py        # Remove duplicate content
│   └── quality_filter.py      # Filter low-quality results
└── pipeline/
    ├── __init__.py
    └── ranking_pipeline.py    # Main pipeline
```

## Installation

```bash
pip install llama-index llama-index-postprocessor-cohere-rerank \
    sentence-transformers torch
```

## Configuration

```python
# layer3_ranking/config.py
from dataclasses import dataclass
from enum import Enum

class RerankerType(Enum):
    COHERE = "cohere"
    BGE_RERANKER = "bge_reranker"
    SIMPLE = "simple"  # Fallback without external API

@dataclass
class RankingConfig:
    # Reranker
    reranker_type: RerankerType = RerankerType.BGE_RERANKER
    reranker_model: str = "BAAI/bge-reranker-large"
    cohere_api_key: str = None  # Set via env COHERE_API_KEY

    # Top-K
    input_top_k: int = 20      # From Layer 2
    output_top_k: int = 5      # To Layer 4

    # Quality thresholds
    min_relevance_score: float = 0.3
    dedup_similarity_threshold: float = 0.85

    # Device
    device: str = "cuda"  # or "cpu"
```

## Reranker Models

### Cohere Reranker (API)

```python
# layer3_ranking/reranker/cohere_reranker.py
from cohere import Client
from typing import List

class CohereReranker:
    """Reranker using Cohere API."""

    def __init__(self, api_key: str, model: str = "rerank-multilingual-v3.0"):
        self.client = Client(api_key=api_key)
        self.model = model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10
    ) -> List[dict]:
        """
        Rerank documents for a query.

        Returns: [{index, relevance_score, document}, ...]
        """
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n
        )

        results = []
        for idx, result in enumerate(response.results):
            results.append({
                "index": result.index,
                "relevance_score": result.relevance_score,
                "document": result.document,
                "text": result.document.get("text", "")
            })

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)
```

### BGE-Reranker (Local)

```python
# layer3_ranking/reranker/bge_reranker.py
import torch
from sentence_transformers import CrossEncoder
from typing import List

class BGEReranker:
    """Reranker using BGE-Reranker model (local)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = CrossEncoder(
            model_name,
            device=device,
            max_length=512
        )
        self.device = device

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[dict]:
        """Rerank documents using cross-encoder."""

        # Prepare query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get relevance scores
        scores = self.model.predict(pairs)

        # Create results
        results = []
        for idx, score in enumerate(scores):
            results.append({
                "index": idx,
                "relevance_score": float(score),
                "document": documents[idx]
            })

        # Sort by score descending
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
```

### Simple Reranker (Fallback)

```python
# layer3_ranking/reranker/simple_reranker.py
from typing import List

class SimpleReranker:
    """Simple keyword-based reranker as fallback."""

    def rerank(
        self,
        query: str,
        documents: List[dict],
        top_k: int = 5
    ) -> List[dict]:
        """Rerank based on keyword overlap."""

        query_terms = set(query.lower().split())

        results = []
        for doc in documents:
            text = doc.get("text", "").lower()
            doc_terms = set(text.split())

            # Jaccard similarity
            overlap = len(query_terms & doc_terms)
            score = overlap / len(query_terms | doc_terms) if query_terms | doc_terms else 0

            results.append({
                "index": doc.get("id"),
                "relevance_score": score,
                "document": doc
            })

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
```

## Quality Filters

### Deduplicator

```python
# layer3_ranking/filter/deduplicator.py
from typing import List
from difflib import SequenceMatcher

class ContentDeduplicator:
    """Remove near-duplicate documents."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold

    def deduplicate(self, documents: List[dict]) -> List[dict]:
        """Remove duplicates while preserving order."""
        if not documents:
            return []

        unique = [documents[0]]

        for doc in documents[1:]:
            is_duplicate = False

            for unique_doc in unique:
                similarity = self._compute_similarity(
                    doc.get("text", ""),
                    unique_doc.get("text", "")
                )

                if similarity >= self.threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(doc)

        return unique

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts."""
        return SequenceMatcher(None, text1, text2).ratio()
```

### Quality Filter

```python
# layer3_ranking/filter/quality_filter.py
import re

class QualityFilter:
    """Filter out low-quality documents."""

    def __init__(
        self,
        min_length: int = 50,
        min_relevance: float = 0.3
    ):
        self.min_length = min_length
        self.min_relevance = min_relevance

    def filter(self, documents: List[dict]) -> List[dict]:
        """Filter documents based on quality criteria."""
        filtered = []

        for doc in documents:
            text = doc.get("text", "") or doc.get("document", {}).get("text", "")

            # Check length
            if len(text.strip()) < self.min_length:
                continue

            # Check for gibberish/garbage
            if self._is_low_quality(text):
                continue

            # Check relevance score
            score = doc.get("relevance_score", 0)
            if score < self.min_relevance:
                continue

            filtered.append(doc)

        return filtered

    def _is_low_quality(self, text: str) -> bool:
        """Check if text is low quality."""
        # Too many special characters
        special_ratio = len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
        if special_ratio > 0.3:
            return True

        # Too few words
        word_count = len(text.split())
        if word_count < 5:
            return True

        return False
```

## Ranking Pipeline

```python
# layer3_ranking/pipeline/ranking_pipeline.py
from typing import List
from ..reranker import CohereReranker, BGEReranker, SimpleReranker
from ..reranker.base_reranker import BaseReranker
from ..filter import ContentDeduplicator, QualityFilter
from ..config import RankingConfig, RerankerType

class RankingPipeline:
    """Main ranking pipeline combining reranker and filters."""

    def __init__(self, config: RankingConfig):
        self.config = config
        self.reranker = self._init_reranker(config)
        self.deduplicator = ContentDeduplicator(
            similarity_threshold=config.dedup_similarity_threshold
        )
        self.quality_filter = QualityFilter(
            min_relevance=config.min_relevance_score
        )

    def _init_reranker(self, config: RankingConfig) -> BaseReranker:
        """Initialize reranker based on config."""
        if config.reranker_type == RerankerType.COHERE:
            return CohereReranker(
                api_key=config.cohere_api_key
            )
        elif config.reranker_type == RerankerType.BGE_RERANKER:
            return BGEReranker(
                model_name=config.reranker_model,
                device=config.device
            )
        else:
            return SimpleReranker()

    def process(
        self,
        query: str,
        documents: List[dict]
    ) -> List[dict]:
        """
        Process documents through ranking pipeline.

        Steps:
        1. Extract text from documents
        2. Rerank using configured reranker
        3. Deduplicate
        4. Quality filter
        5. Return top-k
        """
        # Extract texts
        texts = []
        for doc in documents:
            text = doc.get("text") or doc.get("content", "")
            if isinstance(doc.get("document"), dict):
                text = doc["document"].get("text", text)
            texts.append(text)

        # Rerank
        reranked = self.reranker.rerank(
            query=query,
            documents=texts,
            top_k=self.config.input_top_k
        )

        # Attach original document metadata
        for result in reranked:
            original_idx = result["index"]
            if original_idx < len(documents):
                result["metadata"] = documents[original_idx].get("metadata", {})

        # Deduplicate
        deduplicated = self.deduplicator.deduplicate(reranked)

        # Quality filter
        filtered = self.quality_filter.filter(deduplicated)

        # Return top-k
        return filtered[:self.config.output_top_k]
```

## Main Entry Point

```python
# layer3_ranking/main.py
import argparse
import json
from .config import RankingConfig, RerankerType
from .pipeline.ranking_pipeline import RankingPipeline

def main():
    parser = argparse.ArgumentParser(description="Layer 3: Ranking & Processing")
    parser.add_argument("--input", type=str, help="Input JSON file with documents")
    parser.add_argument("--query", type=str, required=True, help="Original query")
    parser.add_argument("--reranker", type=str, default="bge", choices=["cohere", "bge", "simple"])
    parser.add_argument("--output-top-k", type=int, default=5)
    args = parser.parse_args()

    # Load documents
    if args.input:
        with open(args.input, "r") as f:
            documents = json.load(f)
    else:
        # Mock documents for testing
        documents = [
            {"id": "1", "text": "Machine learning is a subset of AI"},
            {"id": "2", "text": "Deep learning uses neural networks with multiple layers"},
            {"id": "3", "text": "Python is a popular programming language for ML"},
            {"id": "4", "text": "Natural language processing deals with text"},
            {"id": "5", "text": "Computer vision processes images and videos"},
        ]

    # Map reranker type
    reranker_map = {
        "cohere": RerankerType.COHERE,
        "bge": RerankerType.BGE_RERANKER,
        "simple": RerankerType.SIMPLE
    }

    # Configure
    config = RankingConfig(
        reranker_type=reranker_map[args.reranker],
        output_top_k=args.output_top_k
    )

    # Process
    pipeline = RankingPipeline(config)
    results = pipeline.process(args.query, documents)

    # Output
    print(f"\nQuery: {args.query}")
    print(f"\nTop {len(results)} Reranked Results:")
    for i, result in enumerate(results, 1):
        score = result.get("relevance_score", 0)
        text = result.get("text", result.get("document", {}).get("text", ""))
        print(f"  {i}. [Score: {score:.4f}] {text[:60]}...")

if __name__ == "__main__":
    main()
```

## Testing

```bash
# Test with mock data
python -m layer3_ranking --query "What is machine learning?" --reranker simple

# Test with file input
python -m layer3_ranking \
    --query "What is machine learning?" \
    --input results_from_layer2.json \
    --reranker bge

# Run unit tests
python -c "
from layer3_ranking import RankingPipeline, RankingConfig, RerankerType

config = RankingConfig(reranker_type=RerankerType.SIMPLE)
pipeline = RankingPipeline(config)

documents = [
    {'id': '1', 'text': 'Machine learning is a subset of AI'},
    {'id': '2', 'text': 'Deep learning uses neural networks'},
    {'id': '3', 'text': 'ML algorithms learn from data'},
]

results = pipeline.process('What is ML?', documents)
assert len(results) > 0
print(f'✓ Layer 3 test passed: {len(results)} documents reranked')
"
```

## Layer Communication

Layer 3 receives document list from Layer 2, outputs reranked list to Layer 4.

```python
# Interface between Layer 2 and Layer 3
@dataclass
class Layer2Output:
    query: str
    documents: List[dict]  # From RRF fusion
    query_variants: List[str]  # For debugging

# Interface between Layer 3 and Layer 4
@dataclass
class Layer3Output:
    query: str
    documents: List[dict]  # Reranked, filtered
    scores: List[float]  # Relevance scores
    metadata: dict  # reranker used, timing
```

---

**Previous**: [Layer 2: Query Orchestration](./layer-2-query-orchestration.md)
**Next**: [Layer 4: Synthesis & Memory](./layer-4-synthesis-memory.md)
