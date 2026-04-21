# RAG System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY INPUT                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 4: SYNTHESIS & MEMORY                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐│
│  │   Compact    │  │  Auto Dream │  │      Context Window Manager     ││
│  │   Mode       │  │  (Async)    │  │                                 ││
│  └─────────────┘  └─────────────┘  └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 3: RANKING & PROCESSING                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐│
│  │  LlamaIndex  │  │  Cohere/    │  │       Result Filter &           ││
│  │  Reranker    │  │  BGE-Rerank │  │       Quality Scorer           ││
│  └─────────────┘  └─────────────┘  └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 2: QUERY ORCHESTRATION                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐│
│  │ Multi-Query │  │     HyDE    │  │      Query Transformation        ││
│  │ (3-5 vars)  │  │  (Hypothet.)│  │           Pipeline               ││
│  └─────────────┘  └─────────────┘  └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 1: DATA & INGESTION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐│
│  │  PDF/Docx   │  │  Chunking   │  │        LanceDB                  ││
│  │  Web Scraper│  │  Strategy   │  │     (Serverless Vector DB)       ││
│  └─────────────┘  └─────────────┘  └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────┐
                         │   LLM (GPT-4o   │
                         │    /Claude)     │
                         └─────────────────┘
```

## 4-Layer Architecture

| Layer | Name | Component | Keyword | Status |
|-------|------|-----------|---------|--------|
| 1 | Data & Ingestion | Python + LanceDB | INGESTION | Standalone |
| 2 | Query Orchestration | Multi-Query + HyDE | RETRIEVAL OPTIMIZATION | Standalone |
| 3 | Ranking & Processing | LlamaIndex Reranker | POST-PROCESSING | Standalone |
| 4 | Synthesis & Memory | Compact + Auto Dream | SYNTHESIS & CONSOLIDATION | Standalone |

## Data Flow

```
[Document Input] → [Chunking] → [Embedding] → [LanceDB Storage]
                                                      │
[User Query] → [Multi-Query] → [HyDE Transform] ──────┼──→ [Vector Search]
                                                      │
                           [Top-K Results] → [Reranker] → [Filtered Results]
                                                      │
                                    [Compact] → [LLM Context]
                                                      │
                                         [LLM Response] → [User]
                                                      │
                                         [Session Memory] ←── [Auto Dream]
```

## Layer Independence

Mỗi layer có thể chạy độc lập:

```bash
# Layer 1: Ingestion only
python -m layer1_ingestion --source ./docs --db ./data/lancedb

# Layer 2: Query orchestration only (test with mock data)
python -m layer2_query_orchestration --test-mode

# Layer 3: Ranking only
python -m layer3_ranking --input results.json --reranker cohere

# Layer 4: Memory synthesis
python -m layer4_synthesis --session-id abc123
```

## Configuration

```yaml
# config/system.yaml
layers:
  layer1:
    chunk_size: 512
    chunk_overlap: 50
    embedding_model: "BAAI/bge-small-zh-v1.5"

  layer2:
    multi_query_count: 5
    hyde_enabled: true

  layer3:
    reranker_model: "BAAI/bge-reranker-base"
    top_k: 20
    rerank_top_k: 5

  layer4:
    compact_max_tokens: 4096
    dream_interval_minutes: 30
```

## Project Folder Structure

```
rag-system/
├── docs/                          # Documentation (6 files)
├── src/                           # Source code
│   ├── ingestion/                 # Layer 1: Data & Ingestion
│   ├── query_orchestration/       # Layer 2: Query Orchestration
│   ├── ranking/                   # Layer 3: Ranking & Processing
│   ├── synthesis/                  # Layer 4: Synthesis & Memory
│   └── ui_terminal/               # UI Terminal
├── data/raw/                      # Dataset: PDF, DOCX, TXT
├── requirements.txt               # Python dependencies
└── run.py                        # Main entry point
```

---

## Unified Pipeline (Run All Layers)

### Single Command - Chạy tất cả Layer 1→2→3→4

```bash
# 1 LỆNH DUY NHẤT - chạy tất cả
python run.py --query "Your question here"
```

### Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Ingestion (auto-ingest nếu chưa có data)    │
│  Layer 2: Query Orchestration (Multi-Query + HyDE)     │
│  Layer 3: Ranking (Reranker)                          │
│  Layer 4: Synthesis (Compact + LLM + Memory)          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Response + Sources
```

### Usage Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Single Query** | `python run.py --query "..."` | Chạy 1 câu hỏi |
| **Interactive** | `python run.py` | Chat liên tục trong terminal |
| **Ingest Only** | `python run.py --ingest` | Chỉ ingest documents |
| **Terminal UI** | `python run.py --ui` | Rich terminal interface |

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Ingest data (Layer 1) - chạy 1 lần
python run.py --ingest

# 3. Query (Layer 2-4 tự động)
python run.py --query "What is RAG?"

# 4. Hoặc interactive terminal
python run.py --ui
```

---

**Next**: See [Layer 1: Ingestion](./layer-1-ingestion.md)
