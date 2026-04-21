# UI Streamlit

## Overview

| Property | Value |
|----------|-------|
| Layer | UI |
| Component | Streamlit Web UI |
| Purpose | Web interface for RAG system interaction |
| Tech | Python + Streamlit |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      STREAMLIT WEB UI                        │
└──────────────────────────────────────────────────────────────┘

  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │   Chat      │  │   Ingest    │  │  Settings   │
  │   Page      │  │   Page      │  │   Page      │
  └─────────────┘  └─────────────┘  └─────────────┘
         │                │               │
         └────────────────┼───────────────┘
                          │
                    ┌─────┴─────┐
                    │ RAGClient │
                    └─────┬─────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
  ┌────────────┐   ┌────────────┐   ┌────────────┐
  │  Layer 1  │   │  Layer 2-3 │   │  Layer 4   │
  │ Ingestion  │   │   Query +   │   │ Synthesis │
  │            │   │   Ranking   │   │           │
  └────────────┘   └────────────┘   └────────────┘
```

## Pages

### Chat Page (`01_chat.py`)
- Main chat interface
- Accepts user queries
- Displays assistant responses
- Shows source documents with relevance scores

### Ingest Page (`02_ingest.py`)
- Document ingestion interface
- Configure data directory path
- Trigger Layer 1 ingestion pipeline

### Settings Page (`03_settings.py`)
- Configure embedding model
- Configure reranker options
- LLM model settings

## File Structure

```
ui_streamlit/
├── __init__.py
├── main.py                    # Entry: streamlit run src/ui_streamlit/main.py
├── config.py                  # Streamlit page configuration
├── pages/
│   ├── __init__.py
│   ├── 01_chat.py             # Main chat page
│   ├── 02_ingest.py           # Document ingestion page
│   └── 03_settings.py         # Settings page
├── components/
│   ├── __init__.py
│   ├── chat.py                # Chat message rendering
│   ├── sources.py             # Sources display
│   └── layout.py              # Layout helpers (header, sidebar)
└── utils/
    ├── __init__.py
    └── rag_client.py           # RAGClient - wraps UnifiedPipeline
```

## Usage

```bash
# Run UI directly
streamlit run src/ui_streamlit/main.py --server.headless=true

# Or via run.py
python run.py --ui
```

## Components

### RAGClient
`utils/rag_client.py` — Session-scoped client wrapping the UnifiedPipeline.

```python
client = RAGClient()
result = client.query("What is RAG?")
# result = {
#   "response": "...",
#   "sources": [...],
#   "metadata": {...}
# }
```

### Chat Components
- `render_user_message(message)` — Display user message bubble
- `render_assistant_message(message)` — Display assistant response

### Sources Display
`render_sources(sources)` — Expandable panel showing ranked source documents.

---

**Previous**: [System Architecture](./system-architecture.md)
