# Layer 4: Synthesis & Memory

## Overview

| Property | Value |
|----------|-------|
| Layer | 4 |
| Keyword | SYNTHESIS & CONSOLIDATION |
| Components | Compact Mode + Auto Dream |
| Purpose | Context compression, response synthesis, long-term memory |
| Status | **Standalone** - Can run independently |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  SYNTHESIS & MEMORY PIPELINE                 │
└──────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │  Reranked Docs  │
                         │   (Layer 3)     │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌──────────────────┐       ┌──────────────────┐
         │   Compact Mode    │       │  Session Memory  │
         │   (Context        │       │  (Short-term)    │
         │    Compression)  │       │                  │
         └────────┬─────────┘       └────────┬─────────┘
                  │                          │
                  │   ┌──────────────────────┘
                  │   │
                  ▼   ▼
         ┌──────────────────┐
         │  Response         │
         │  Synthesizer     │
         │  (LLM)           │
         └────────┬─────────┘
                  │
                  ├──────────────────┐
                  │                  │
                  ▼                  ▼
         ┌──────────────┐    ┌──────────────┐
         │    User      │    │  Auto Dream  │
         │   Response   │    │  (Background)│
         └──────────────┘    └──────┬───────┘
                                   │
                                   ▼
                          ┌──────────────┐
                          │ Long-term    │
                          │ Memory       │
                          │ (Permanent)  │
                          └──────────────┘
```

## File Structure

```
layer4_synthesis/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration
├── compact/
│   ├── __init__.py
│   └── context_compactor.py    # Context window compression
├── memory/
│   ├── __init__.py
│   ├── session_memory.py       # Short-term session memory
│   └── auto_dream.py           # Background dreaming process
├── llm/
│   ├── __init__.py
│   └── response_synthesizer.py # LLM response generation
└── pipeline/
    ├── __init__.py
    └── synthesis_pipeline.py   # Main synthesis pipeline
```

## Installation

```bash
pip install llama-index llama-index-llms-openai \
    openai asyncio-modules
```

## Configuration

```python
# layer4_synthesis/config.py
from dataclasses import dataclass
import asyncio

@dataclass
class SynthesisConfig:
    # Compact Mode
    compact_max_tokens: int = 4096
    compact_buffer_tokens: int = 500  # Buffer for response
    compression_strategy: str = "truncate"  # or "summarize"

    # LLM
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    # Response synthesis
    system_prompt: str = """You are a helpful AI assistant.
Use the provided context to answer the user's question.
If the answer is not in the context, say you don't know."""

    # Auto Dream
    dream_enabled: bool = True
    dream_interval_minutes: int = 30
    dream_model: str = "gpt-4o-mini"
    memory_threshold: int = 10  # Process after N interactions

    # Memory
    memory_table: str = "agent_memory"
```

## Compact Mode (Context Compression)

### Purpose

Fit documents into LLM context window while preserving important information.

```python
# layer4_synthesis/compact/context_compactor.py
from typing import List
import tiktoken

class ContextCompactor:
    """Compress context to fit within token limit."""

    def __init__(
        self,
        max_tokens: int = 4096,
        buffer_tokens: int = 500,
        model: str = "gpt-4o"
    ):
        self.max_tokens = max_tokens
        self.buffer_tokens = buffer_tokens
        self.encoder = tiktoken.encoding_for_model(model)

    def compact(
        self,
        documents: List[dict],
        system_prompt: str = ""
    ) -> tuple[str, List[dict]]:
        """
        Compact documents to fit within token limit.

        Returns: (compacted_context, used_documents)
        """
        available_tokens = self.max_tokens - self.buffer_tokens

        # Count system prompt tokens
        if system_prompt:
            available_tokens -= len(self.encoder.encode(system_prompt))

        # Sort documents by relevance score
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        compacted_context = ""
        used_docs = []

        for doc in sorted_docs:
            text = doc.get("text", "") or doc.get("content", "")
            doc_tokens = len(self.encoder.encode(text))

            if doc_tokens <= available_tokens:
                compacted_context += f"\n\n{text}"
                available_tokens -= doc_tokens
                used_docs.append(doc)
            else:
                # Try to fit a portion
                if available_tokens > 100:
                    truncated = self._truncate_to_tokens(text, available_tokens)
                    compacted_context += f"\n\n{truncated}"
                    used_docs.append({**doc, "truncated": True})
                break

        return compacted_context.strip(), used_docs

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        tokens = self.encoder.encode(text)
        truncated_tokens = tokens[:max_tokens]
        return self.encoder.decode(truncated_tokens)
```

### Alternative: Summary-based Compression

```python
class SummaryCompactor:
    """Compress by summarizing long documents."""

    def __init__(self, llm):
        self.llm = llm

    async def compact(
        self,
        documents: List[dict],
        max_tokens: int
    ) -> tuple[str, List[dict]]:
        """Summarize documents that exceed token limit."""
        compacted = []
        total_tokens = 0

        for doc in documents:
            text = doc.get("text", "")
            tokens = len(tiktoken.encode(text))

            if tokens <= max_tokens - total_tokens:
                compacted.append(doc)
                total_tokens += tokens
            else:
                # Summarize
                summary = await self._summarize(text)
                doc["text"] = summary
                doc["original_length"] = tokens
                doc["summarized"] = True
                compacted.append(doc)
                total_tokens += len(tiktoken.encode(summary))

        return "\n\n".join(d["text"] for d in compacted), compacted

    async def _summarize(self, text: str) -> str:
        """Generate summary of text."""
        prompt = f"Summarize the following concisely:\n\n{text}"
        response = await self.llm.acomplete(prompt)
        return response.text
```

## Session Memory

### Purpose

Remember conversation history within a session.

```python
# layer4_synthesis/memory/session_memory.py
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import json

@dataclass
class MemoryEntry:
    """Single memory entry."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    query: Optional[str] = None
    response: Optional[str] = None
    sources: List[dict] = field(default_factory=list)

class SessionMemory:
    """Manage short-term conversation memory."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: List[MemoryEntry] = []
        self.interaction_count = 0

    def add(
        self,
        role: str,
        content: str,
        query: str = None,
        response: str = None,
        sources: List[dict] = None
    ):
        """Add entry to memory."""
        import time

        entry = MemoryEntry(
            role=role,
            content=content,
            timestamp=time.time(),
            query=query,
            response=response,
            sources=sources or []
        )
        self.entries.append(entry)
        self.interaction_count += 1

    def get_context(self, max_entries: int = 5) -> str:
        """Get recent conversation context."""
        recent = self.entries[-max_entries:]
        context = []

        for entry in recent:
            if entry.role == "user":
                context.append(f"User: {entry.content}")
            else:
                context.append(f"Assistant: {entry.content}")

        return "\n".join(context)

    def get_full_history(self) -> List[dict]:
        """Get full conversation history."""
        return [
            {
                "role": e.role,
                "content": e.content,
                "timestamp": e.timestamp,
                "sources": e.sources
            }
            for e in self.entries
        ]

    def clear(self):
        """Clear session memory."""
        self.entries = []
        self.interaction_count = 0

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "session_id": self.session_id,
            "entries": [
                {
                    "role": e.role,
                    "content": e.content,
                    "timestamp": e.timestamp,
                    "query": e.query,
                    "response": e.response,
                    "sources": e.sources
                }
                for e in self.entries
            ],
            "interaction_count": self.interaction_count
        }
```

## Auto Dream (Long-term Memory)

### Concept

After each session or at intervals, the system "dreams" - processing and consolidating important information into long-term memory.

```python
# layer4_synthesis/memory/auto_dream.py
import asyncio
from typing import List, Optional
from datetime import datetime

class AutoDream:
    """
    Background memory consolidation process.

    Runs asynchronously to not block user interaction.
    """

    def __init__(
        self,
        llm,
        memory_store,
        config
    ):
        self.llm = llm
        self.memory_store = memory_store  # LanceDB or similar
        self.config = config
        self.last_dream_time = None
        self.is_running = False

    async def dream(self, session_memory: 'SessionMemory'):
        """
        Process session memory and consolidate into long-term memory.

        Steps:
        1. Extract key facts from conversation
        2. Identify contradictions
        3. Update/merge with existing memory
        4. Clean up old/unimportant entries
        """
        if not self.config.dream_enabled:
            return

        print(f"[Dream] Starting memory consolidation...")

        # Extract key information
        key_facts = await self._extract_key_facts(session_memory)

        # Find contradictions
        contradictions = await self._find_contradictions(key_facts)

        # Resolve contradictions
        if contradictions:
            resolved = await self._resolve_contradictions(contradictions)
            key_facts = self._merge_resolved(key_facts, resolved)

        # Consolidate into memory
        await self._consolidate_memory(key_facts)

        # Cleanup old entries
        await self._cleanup_old_entries()

        self.last_dream_time = datetime.now()
        print(f"[Dream] Consolidation complete. {len(key_facts)} facts stored.")

    async def _extract_key_facts(self, session: 'SessionMemory') -> List[dict]:
        """Extract key facts from conversation."""
        history = session.get_full_history()

        prompt = f"""Analyze this conversation and extract key facts, entities,
and important information. Format as JSON list of facts.

Conversation:
{json.dumps(history, indent=2)}

Extract facts in format:
[{{"fact": "...", "category": "...", "importance": "high/medium/low"}}]"""

        response = await self.llm.acomplete(prompt)

        try:
            facts = json.loads(response.text)
            return facts
        except:
            return []

    async def _find_contradictions(self, facts: List[dict]) -> List[dict]:
        """Find contradictory facts."""
        contradictions = []

        for i, fact1 in enumerate(facts):
            for fact2 in facts[i+1:]:
                if self._are_contradictory(fact1["fact"], fact2["fact"]):
                    contradictions.append({
                        "fact1": fact1,
                        "fact2": fact2
                    })

        return contradictions

    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """Simple contradiction detection."""
        # Check for negation keywords
        neg_words = ["not", "no", "never", "don't", "doesn't", "isn't"]
        has_neg1 = any(w in text1.lower() for w in neg_words)
        has_neg2 = any(w in text2.lower() for w in neg_words)

        # Simple check: same content but different negation
        if has_neg1 != has_neg2:
            base1 = " ".join(w for w in text1.split() if w.lower() not in neg_words)
            base2 = " ".join(w for w in text2.split() if w.lower() not in neg_words)
            if base1.strip() == base2.strip():
                return True

        return False

    async def _resolve_contradictions(self, contradictions: List[dict]) -> dict:
        """Resolve contradictions using LLM."""
        prompt = f"""Resolve these contradictory facts. Return the correct version.

Contradictions:
{json.dumps(contradictions, indent=2)}

Return JSON: {{"resolved_fact": "...", "reasoning": "..."}}"""

        response = await self.llm.acomplete(prompt)
        return json.loads(response.text)

    async def _consolidate_memory(self, facts: List[dict]):
        """Store facts in long-term memory."""
        for fact in facts:
            await self.memory_store.add(
                entity_type="fact",
                content=fact["fact"],
                category=fact.get("category", "general"),
                importance=fact.get("importance", "medium"),
                embedding=await self._embed(fact["fact"])
            )

    async def _cleanup_old_entries(self):
        """Remove low-importance old entries."""
        await self.memory_store.prune(
            keep_importance=["high", "medium"],
            max_entries=1000
        )

    async def _embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        # Use embedding model
        from layer1_ingestion.embedding import BGEEmbeddings
        embedder = BGEEmbeddings()
        return embedder.embed([text])[0]
```

## Response Synthesizer

```python
# layer4_synthesis/llm/response_synthesizer.py
from typing import List, Optional
import asyncio

class ResponseSynthesizer:
    """Generate responses using LLM with context."""

    def __init__(self, llm, config):
        self.llm = llm
        self.config = config

    async def synthesize(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None
    ) -> str:
        """
        Synthesize response from query and context.

        Args:
            query: User's question
            context: Compacted document context
            conversation_history: Optional previous conversation

        Returns:
            Generated response string
        """
        # Build prompt
        prompt_parts = []

        if conversation_history:
            prompt_parts.append(f"Previous conversation:\n{conversation_history}\n")

        prompt_parts.append(f"Context:\n{context}\n")
        prompt_parts.append(f"Question: {query}\n")
        prompt_parts.append("Answer:")

        full_prompt = "\n".join(prompt_parts)

        # Generate response
        response = await self.llm.acomplete(
            prompt=full_prompt,
            system_prompt=self.config.system_prompt,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )

        return response.text

    def synthesize_sync(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None
    ) -> str:
        """Synchronous version."""
        return asyncio.run(self.synthesize(query, context, conversation_history))
```

## Synthesis Pipeline

```python
# layer4_synthesis/pipeline/synthesis_pipeline.py
import asyncio
from typing import List
from ..compact.context_compactor import ContextCompactor
from ..memory.session_memory import SessionMemory
from ..memory.auto_dream import AutoDream
from ..llm.response_synthesizer import ResponseSynthesizer
from ..config import SynthesisConfig

class SynthesisPipeline:
    """Main synthesis pipeline combining all Layer 4 components."""

    def __init__(self, llm, memory_store, config: SynthesisConfig):
        self.llm = llm
        self.memory_store = memory_store
        self.config = config

        self.compactor = ContextCompactor(
            max_tokens=config.compact_max_tokens,
            buffer_tokens=config.compact_buffer_tokens
        )
        self.synthesizer = ResponseSynthesizer(llm, config)
        self.auto_dream = AutoDream(llm, memory_store, config)

        # Session memories
        self.sessions: dict[str, SessionMemory] = {}

    def get_or_create_session(self, session_id: str) -> SessionMemory:
        """Get or create session memory."""
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id)
        return self.sessions[session_id]

    async def process(
        self,
        query: str,
        documents: List[dict],
        session_id: str,
        conversation_history: str = None
    ) -> tuple[str, dict]:
        """
        Process query through full synthesis pipeline.

        Returns: (response, metadata)
        """
        # Get session
        session = self.get_or_create_session(session_id)

        # Compact context
        context, used_docs = self.compactor.compact(
            documents=documents,
            system_prompt=self.config.system_prompt
        )

        # Synthesize response
        response = await self.synthesizer.synthesize(
            query=query,
            context=context,
            conversation_history=conversation_history
        )

        # Update session memory
        session.add(
            role="user",
            content=query,
            query=query
        )
        session.add(
            role="assistant",
            content=response,
            response=response,
            sources=used_docs
        )

        # Trigger Auto Dream if threshold reached
        if (self.config.dream_enabled and
            session.interaction_count >= self.config.memory_threshold):
            asyncio.create_task(self.auto_dream.dream(session))

        return response, {
            "session_id": session_id,
            "used_documents": len(used_docs),
            "context_tokens": len(context.split()),
            "auto_dream_triggered": session.interaction_count >= self.config.memory_threshold
        }

    async def dream_now(self, session_id: str):
        """Manually trigger Auto Dream for a session."""
        if session_id in self.sessions:
            await self.auto_dream.dream(self.sessions[session_id])
```

## Main Entry Point

```python
# layer4_synthesis/main.py
import argparse
import asyncio
import json
from .config import SynthesisConfig
from .pipeline.synthesis_pipeline import SynthesisPipeline

# Mock LLM for testing
class MockLLM:
    async def acomplete(self, prompt, **kwargs):
        class Response:
            text = "This is a mock response based on the context provided."
        return Response()

def main():
    parser = argparse.ArgumentParser(description="Layer 4: Synthesis & Memory")
    parser.add_argument("--query", type=str, required=True, help="User query")
    parser.add_argument("--docs", type=str, help="JSON file with documents")
    parser.add_argument("--session", type=str, default="default", help="Session ID")
    parser.add_argument("--no-dream", action="store_true", help="Disable Auto Dream")
    args = parser.parse_args()

    # Load documents
    if args.docs:
        with open(args.docs, "r") as f:
            documents = json.load(f)
    else:
        documents = [
            {"text": "Machine learning is a subset of AI.", "relevance_score": 0.9},
            {"text": "Deep learning uses neural networks.", "relevance_score": 0.8},
        ]

    # Configure
    config = SynthesisConfig(dream_enabled=not args.no_dream)
    pipeline = SynthesisPipeline(
        llm=MockLLM(),
        memory_store=None,  # Not used in mock
        config=config
    )

    # Process
    response, metadata = asyncio.run(
        pipeline.process(args.query, documents, args.session)
    )

    print(f"\nQuery: {args.query}")
    print(f"Response: {response}")
    print(f"Metadata: {metadata}")

if __name__ == "__main__":
    main()
```

## Testing

```bash
# Test synthesis only
python -m layer4_synthesis --query "What is ML?" --no-dream

# Test with full pipeline
python -m layer4_synthesis \
    --query "What is machine learning?" \
    --docs results_from_layer3.json \
    --session test_session

# Test Auto Dream
python -c "
import asyncio
from layer4_synthesis import SynthesisPipeline, SynthesisConfig, SessionMemory, AutoDream

class MockLLM:
    async def acomplete(self, prompt, **kwargs):
        class Response:
            text = 'Mock response'
        return Response()

config = SynthesisConfig(dream_enabled=True, memory_threshold=2)
session = SessionMemory('test')
session.add('user', 'What is AI?')
session.add('assistant', 'AI is artificial intelligence.')

# Test dream
dream = AutoDream(MockLLM(), None, config)
asyncio.run(dream.dream(session))
print('✓ Layer 4 Auto Dream test passed')
"
```

## Layer Communication

Layer 4 receives reranked documents from Layer 3, outputs final response.

```python
# Interface between Layer 3 and Layer 4
@dataclass
class Layer3Output:
    query: str
    documents: List[dict]
    scores: List[float]

# Layer 4 Output
@dataclass
class Layer4Output:
    response: str
    session_id: str
    sources: List[dict]
    metadata: dict  # tokens used, dream triggered, etc.
```

---

**Previous**: [Layer 3: Ranking & Processing](./layer-3-ranking-processing.md)
**Next**: [UI Terminal](./ui-terminal.md)
