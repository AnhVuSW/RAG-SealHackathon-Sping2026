# Layer 1: Data & Ingestion

## Overview

| Property | Value |
|----------|-------|
| Layer | 1 |
| Keyword | INGESTION |
| Components | Python + LanceDB |
| Purpose | Document ingestion, chunking, embedding, storage |
| Status | **Standalone** - Can run independently |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     DATA INGESTION PIPELINE                   │
└──────────────────────────────────────────────────────────────┘

  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │   PDF    │   │  Docx    │   │   Web    │   │  Custom  │
  │  Loader  │   │  Loader  │   │  Scraper │   │  Loader  │
  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Semantic       │
                   │  Chunking       │
                   │  (512 tokens)   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  BGE Embedding  │
                   │  (bge-large)    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    LanceDB      │
                   │  (Vector Store) │
                   └─────────────────┘
```

## File Structure

```
layer1_ingestion/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration
├── loaders/
│   ├── __init__.py
│   ├── base_loader.py         # Abstract base class
│   ├── pdf_loader.py          # PDF processing
│   ├── docx_loader.py         # DOCX processing
│   └── web_loader.py          # Web scraping
├── chunking/
│   ├── __init__.py
│   ├── semantic_chunker.py    # Semantic chunking strategy
│   └── sliding_window.py      # Sliding window strategy
├── embedding/
│   ├── __init__.py
│   └── bge_embeddings.py      # BGE embedding model
└── storage/
    ├── __init__.py
    └── lancedb_writer.py      # LanceDB writer
```

## Installation

```bash
pip install lancedb llama-index-readers-file \
    pypdf python-docx requests beautifulsoup4 \
    sentence-transformers
```

## Configuration

```python
# layer1_ingestion/config.py
from dataclasses import dataclass

@dataclass
class IngestionConfig:
    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_device: str = "cuda"  # or "cpu"

    # LanceDB
    lancedb_uri: str = "./data/lancedb"
    lancedb_table: str = "documents"

    # Processing
    batch_size: int = 100
    num_workers: int = 4
```

## Usage

### Basic Usage

```python
from layer1_ingestion import DocumentIngestionPipeline

# Initialize pipeline
pipeline = DocumentIngestionPipeline(
    config=IngestionConfig(),
    embedding_model="BAAI/bge-small-zh-v1.5"
)

# Ingest documents
results = pipeline.ingest(
    source="./documents",
    file_types=["pdf", "docx", "txt"]
)

print(f"Ingested {results.total_chunks} chunks from {results.total_docs} documents")
```

### Standalone Execution

```bash
# Run as standalone module
python -m layer1_ingestion --source ./docs --db ./data/lancedb

# With options
python -m layer1_ingestion \
    --source ./documents \
    --db ./data/lancedb \
    --chunk-size 512 \
    --overlap 50 \
    --model BAAI/bge-small-zh-v1.5
```

## Loaders

### PDF Loader

```python
# layer1_ingestion/loaders/pdf_loader.py
from llama_index.readers.file import PDFReader
from pathlib import Path

class PDFLoader:
    def __init__(self):
        self.reader = PDFReader()

    def load(self, file_path: Path) -> list[str]:
        """Load and extract text from PDF."""
        documents = self.reader.load_file(file_path)
        return [doc.text for doc in documents]

    def load_pages(self, file_path: Path) -> list[tuple[int, str]]:
        """Load PDF page by page with page numbers."""
        documents = self.reader.load_file(file_path)
        return [(i+1, doc.text) for i, doc in enumerate(documents)]
```

### Web Loader

```python
# layer1_ingestion/loaders/web_loader.py
import requests
from bs4 import BeautifulSoup
from typing import Iterator

class WebLoader:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def load(self, url: str) -> str:
        """Load content from a single URL."""
        response = requests.get(url, timeout=self.timeout)
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)

    def load_many(self, urls: list[str]) -> Iterator[tuple[str, str]]:
        """Load content from multiple URLs."""
        for url in urls:
            try:
                content = self.load(url)
                yield url, content
            except Exception as e:
                print(f"Failed to load {url}: {e}")
                continue
```

## Chunking Strategy

```python
# layer1_ingestion/chunking/semantic_chunker.py
from typing import Iterator
import re

class SemanticChunker:
    """Split text by semantic boundaries (sentences, paragraphs)."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        split_by: str = "sentence"  # or "paragraph"
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.split_by = split_by

    def chunk(self, text: str, metadata: dict = None) -> Iterator[dict]:
        """Yield chunks with metadata."""
        if self.split_by == "sentence":
            units = self._split_sentences(text)
        else:
            units = self._split_paragraphs(text)

        current_chunk = []
        current_size = 0

        for unit in units:
            unit_size = len(unit)

            if current_size + unit_size > self.chunk_size and current_chunk:
                yield self._create_chunk(current_chunk, metadata)

                # Handle overlap
                overlap_text = current_chunk[-1]
                current_chunk = [overlap_text] if self.overlap > 0 else []
                current_size = len(overlap_text) if self.overlap > 0 else 0

            current_chunk.append(unit)
            current_size += unit_size

        if current_chunk:
            yield self._create_chunk(current_chunk, metadata)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        pattern = r'(?<=[。！？.!?])\s+'
        return re.split(pattern, text)

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        return [p.strip() for p in text.split("\n\n") if p.strip()]
```

## Embedding

```python
# layer1_ingestion/embedding/bge_embeddings.py
from sentence_transformers import SentenceTransformer
import torch

class BGEEmbeddings:
    """BGE embedding model wrapper."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        return self.embed([query])[0]
```

## LanceDB Storage

```python
# layer1_ingestion/storage/lancedb_writer.py
import lancedb
from pathlib import Path
import pyarrow as pa

class LanceDBWriter:
    """Write documents to LanceDB."""

    def __init__(self, uri: str, table_name: str = "documents"):
        self.uri = uri
        self.table_name = table_name
        self.db = lancedb.connect(uri)

    def create_table(self, schema: pa.Schema):
        """Create table if not exists."""
        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)

        table = self.db.create_table(self.table_name, schema=schema)
        return table

    def write(self, chunks: list[dict]):
        """Write chunks to LanceDB."""
        table = self.db.open_table(self.table_name)
        table.add(chunks)

    def write_batch(self, chunks: list[dict], batch_size: int = 100):
        """Write chunks in batches."""
        table = self.db.open_table(self.table_name)

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            table.add(batch)
            print(f"Written {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

# Schema definition
DOCUMENT_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("text", pa.string()),
    pa.field("metadata", pa.string()),  # JSON serialized
    pa.field("embedding", pa.list_(pa.float32(), 1024)),  # BGE-large dim
])
```

## Main Entry Point

```python
# layer1_ingestion/main.py
import argparse
from pathlib import Path
from .config import IngestionConfig
from .loaders import PDFLoader, DocxLoader, WebLoader
from .chunking import SemanticChunker
from .embedding import BGEEmbeddings
from .storage import LanceDBWriter

def main():
    parser = argparse.ArgumentParser(description="Layer 1: Document Ingestion")
    parser.add_argument("--source", type=str, required=True, help="Source directory or URL")
    parser.add_argument("--db", type=str, default="./data/lancedb", help="LanceDB path")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=50)
    args = parser.parse_args()

    # Initialize components
    config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        lancedb_uri=args.db
    )

    embeddings = BGEEmbeddings()
    chunker = SemanticChunker(chunk_size=config.chunk_size, overlap=config.overlap)
    writer = LanceDBWriter(uri=config.lancedb_uri)

    # Load documents
    source = Path(args.source)
    if source.is_dir():
        documents = load_directory(source)
    else:
        documents = [{"path": str(source), "text": load_file(source)}]

    # Process and store
    chunks = []
    for doc in documents:
        for chunk in chunker.chunk(doc["text"], {"source": doc["path"]}):
            chunk["embedding"] = embeddings.embed([chunk["text"]])[0]
            chunks.append(chunk)

    writer.write(chunks)
    print(f"✓ Ingested {len(chunks)} chunks into LanceDB")

if __name__ == "__main__":
    main()
```

## Testing

```bash
# Test ingestion pipeline
python -c "
from layer1_ingestion import DocumentIngestionPipeline, IngestionConfig

config = IngestionConfig()
pipeline = DocumentIngestionPipeline(config)

# Test with sample data
result = pipeline.ingest(source='./tests/sample_docs')
assert result.total_chunks > 0
print('✓ Layer 1 ingestion test passed')
"
```

## Layer Communication

Layer 1 outputs to LanceDB. Layer 2 reads from LanceDB.

```python
# Interface between Layer 1 and Layer 2
from layer1_ingestion.storage import LanceDBWriter

# Layer 2 reads from the same LanceDB
class LanceDBReader:
    def __init__(self, uri: str):
        self.db = lancedb.connect(uri)

    def search(self, query_embedding: list[float], top_k: int = 10):
        table = self.db.open_table("documents")
        return table.search(query_embedding).limit(top_k).to_list()
```

---

**Previous**: [System Architecture](./system-architecture.md)
**Next**: [Layer 2: Query Orchestration](./layer-2-query-orchestration.md)
