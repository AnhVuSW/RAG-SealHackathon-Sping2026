# UI Terminal (Rich)

## Overview

| Property | Value |
|----------|-------|
| Layer | UI |
| Component | Rich (Python library) |
| Purpose | Terminal UI for user interaction |
| Tech | Python + Rich + Asyncio |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      TERMINAL UI LAYER                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      Rich Console                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Header     │  │   Status     │  │   Help       │     │
│  │   Panel      │  │   Bar        │  │   Panel      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      Chat Interface                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [User] Query displayed here                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Assistant] Response with sources                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Sources: [1] doc1.pdf [0.95] [2] doc2.pdf [0.87]    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      Input Area                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  > Enter your query...                          [Send]│   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## File Structure

```
ui_terminal/
├── __init__.py
├── main.py                    # Entry point
├── console/
│   ├── __init__.py
│   ├── console_manager.py    # Rich console setup
│   ├── layout.py              # Layout management
│   └── themes.py              # Color themes
├── components/
│   ├── __init__.py
│   ├── header.py              # App header
│   ├── chat_bubble.py          # Chat message bubbles
│   ├── sources_panel.py        # Sources display
│   └── input_prompt.py         # Input area
├── pipeline/
│   ├── __init__.py
│   └── terminal_pipeline.py   # Connect to RAG pipeline
└── utils/
    ├── __init__.py
    └── markdown.py            # Markdown rendering
```

## Installation

```bash
pip install rich asyncio-queue
```

## Console Manager

```python
# ui_terminal/console/console_manager.py
from rich.console import Console
from rich.theme import Theme
from typing import Optional

class ConsoleManager:
    """Manage Rich console with custom theme."""

    def __init__(self, theme: Optional[Theme] = None):
        self.theme = theme or self._default_theme()
        self.console = Console(theme=self.theme)

    def _default_theme(self) -> Theme:
        """Default theme for RAG Terminal."""
        return Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "red bold",
            "success": "green",
            "user": "bold blue",
            "assistant": "white",
            "source": "dim",
            "header": "bold magenta",
        })

    def print_header(self, title: str, subtitle: str = ""):
        """Print application header."""
        from rich.panel import Panel
        from rich.text import Text

        header_text = Text(title, style="header")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="dim")

        self.console.print(Panel(header_text, expand=False))

    def clear(self):
        """Clear console."""
        self.console.clear()
```

## Header Component

```python
# ui_terminal/components/header.py
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout

def create_header() -> Panel:
    """Create application header."""

    header_content = Text()
    header_content.append("🔍 RAG Terminal\n", style="bold cyan")
    header_content.append("Retrieval-Augmented Generation System\n", style="dim")
    header_content.append("Layers: Ingestion → Query → Rank → Synthesize", style="info")

    return Panel(
        header_content,
        title="[bold]Red Team Gang[/bold] Hackathon 2026",
        border_style="cyan",
        expand=False
    )

def create_status_bar(
    session_id: str,
    doc_count: int,
    latency_ms: float
) -> Panel:
    """Create status bar showing system state."""

    status = Text()
    status.append(f"Session: {session_id} | ", style="dim")
    status.append(f"Documents: {doc_count} | ", style="dim")
    status.append(f"Latency: {latency_ms:.0f}ms", style="dim")

    return Panel(status, expand=False, border_style="dim")
```

## Chat Bubbles

```python
# ui_terminal/components/chat_bubble.py
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

def create_user_bubble(query: str) -> Panel:
    """Create user message bubble."""
    return Panel(
        Text(query, style="white"),
        box=ROUNDED,
        border_style="blue",
        padding=(0, 1),
        style="on #1e1e1e"
    )

def create_assistant_bubble(
    response: str,
    sources: list = None,
    latency_ms: float = 0
) -> Panel:
    """Create assistant response bubble."""
    content = Text()
    content.append(response, style="white")
    content.append(f"\n\n[Latency: {latency_ms:.0f}ms]", style="dim")

    if sources:
        content.append("\n\n[SOURCES]", style="bold yellow")
        for i, src in enumerate(sources, 1):
            score = src.get("score", 0)
            name = src.get("name", src.get("id", f"doc_{i}"))
            content.append(f"\n  {i}. {name} [{score:.2f}]", style="source")

    return Panel(
        content,
        box=ROUNDED,
        border_style="green",
        padding=(0, 1),
        style="on #1e1e1e"
    )

def create_error_bubble(error: str) -> Panel:
    """Create error message bubble."""
    return Panel(
        Text(error, style="red"),
        box=ROUNDED,
        border_style="red",
        title="[Error]",
        style="on #1e1e1e"
    )

def create_thinking_bubble() -> Panel:
    """Create thinking indicator."""
    from rich.live import Live
    from rich.text import Text

    thinking = Text()
    thinking.append("🤔 ", style="yellow")
    thinking.append("Processing...", style="dim")

    return Panel(
        thinking,
        box=ROUNDED,
        border_style="yellow",
        style="on #1e1e1e"
    )
```

## Input Prompt

```python
# ui_terminal/components/input_prompt.py
from rich.console import Console
from rich.text import Text
from typing import Optional

class InputPrompt:
    """Styled input prompt for user queries."""

    def __init__(self, console: Console):
        self.console = console

    def get_input(self) -> Optional[str]:
        """Get user input with styled prompt."""
        self.console.print()
        user_input = self.console.input(
            "[bold blue]❯[/bold blue] ",
            markup=True
        )
        return user_input.strip() if user_input else None

    def get_multiline_input(self) -> Optional[str]:
        """Get multiline input (end with empty line)."""
        self.console.print("[dim]Enter query (empty line to submit):[/dim]")

        lines = []
        while True:
            line = self.console.input()
            if not line.strip():
                break
            lines.append(line)

        return "\n".join(lines).strip() if lines else None
```

## Sources Panel

```python
# ui_terminal/components/sources_panel.py
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def create_sources_table(sources: list[dict]) -> Table:
    """Create a table showing sources with relevance scores."""

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Source", style="cyan")
    table.add_column("Relevance", justify="right")
    table.add_column("Preview", style="dim")

    for i, src in enumerate(sources, 1):
        name = src.get("name", src.get("id", f"Document {i}"))
        score = src.get("relevance_score", src.get("score", 0))
        preview = src.get("text", "")[:50] + "..." if len(src.get("text", "")) > 50 else src.get("text", "")

        # Color code score
        if score >= 0.8:
            score_style = "green"
        elif score >= 0.6:
            score_style = "yellow"
        else:
            score_style = "red"

        table.add_row(
            str(i),
            name,
            f"[{score_style}]{score:.2f}[/{score_style}]",
            preview
        )

    return table

def create_sources_panel(sources: list[dict]) -> Panel:
    """Create sources panel with table."""
    if not sources:
        return Panel(
            Text("No sources available", style="dim"),
            title="Sources",
            border_style="dim"
        )

    table = create_sources_table(sources)
    return Panel(
        table,
        title=f"[bold]Sources ({len(sources)})[/bold]",
        border_style="cyan",
        expand=False
    )
```

## Markdown Rendering

```python
# ui_terminal/utils/markdown.py
from rich.markdown import Markdown
from rich.text import Text

def render_markdown(text: str) -> Markdown:
    """Render markdown text for Rich."""
    return Markdown(text, style="white")

def render_code_block(code: str, language: str = "") -> Panel:
    """Render code block with syntax highlighting hint."""
    from rich.box import ROUNDED

    label = f"Code ({language})" if language else "Code"
    return Panel(
        Text(code, style="cyan"),
        title=label,
        box=ROUNDED,
        border_style="blue"
    )

def render_bullet_list(items: list[str]) -> Text:
    """Render bullet list."""
    text = Text()
    for item in items:
        text.append(f"  • {item}\n", style="white")
    return text

def render_numbered_list(items: list[str]) -> Text:
    """Render numbered list."""
    text = Text()
    for i, item in enumerate(items, 1):
        text.append(f"  {i}. {item}\n", style="white")
    return text
```

## Terminal Pipeline

```python
# ui_terminal/pipeline/terminal_pipeline.py
import asyncio
from typing import Optional
from dataclasses import dataclass

@dataclass
class PipelineResult:
    response: str
    sources: list[dict]
    latency_ms: float
    session_id: str

class TerminalPipeline:
    """Connect terminal UI to RAG pipeline."""

    def __init__(
        self,
        layer1,  # Ingestion
        layer2,  # Query Orchestration
        layer3,  # Ranking
        layer4   # Synthesis
    ):
        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer4 = layer4
        self.session_id = "default"

    async def process_query(self, query: str) -> PipelineResult:
        """Process query through all 4 layers."""
        import time
        start = time.time()

        # Layer 1: Get from vector store (query embedding)
        query_embedding = self.layer2.embed_model.embed([query])[0]

        # Layer 2: Query orchestration
        docs = self.layer2.pipeline.process(query)

        # Layer 3: Ranking
        reranked = self.layer3.pipeline.process(query, docs)

        # Layer 4: Synthesis
        response, metadata = await self.layer4.pipeline.process(
            query=query,
            documents=reranked,
            session_id=self.session_id
        )

        latency_ms = (time.time() - start) * 1000

        return PipelineResult(
            response=response,
            sources=[
                {"name": d.get("name", d.get("id", "unknown")), "score": d.get("relevance_score", 0)}
                for d in reranked[:5]
            ],
            latency_ms=latency_ms,
            session_id=self.session_id
        )
```

## Main Application

```python
# ui_terminal/main.py
import asyncio
from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from .console.console_manager import ConsoleManager
from .components.header import create_header, create_status_bar
from .components.chat_bubble import (
    create_user_bubble,
    create_assistant_bubble,
    create_error_bubble,
    create_thinking_bubble
)
from .components.input_prompt import InputPrompt
from .components.sources_panel import create_sources_panel
from .pipeline.terminal_pipeline import TerminalPipeline

class RAGTerminal:
    """Main terminal application."""

    def __init__(self, pipeline: TerminalPipeline):
        self.pipeline = pipeline
        self.console_manager = ConsoleManager()
        self.console = self.console_manager.console
        self.input_prompt = InputPrompt(self.console)
        self.chat_history = []

    def render(self):
        """Render the terminal UI."""
        self.console_manager.clear()
        self.console.print(create_header())
        self.console.print()

        # Print chat history
        for role, content, sources, latency in self.chat_history:
            if role == "user":
                self.console.print(create_user_bubble(content))
            else:
                self.console.print(create_assistant_bubble(content, sources, latency))
            self.console.print()

        # Status bar
        self.console.print(create_status_bar(
            session_id=self.pipeline.session_id,
            doc_count=0,  # Would come from layer1
            latency_ms=0
        ))

    def print_welcome(self):
        """Print welcome message."""
        self.console_manager.clear()
        self.console.print(create_header())
        self.console.print()
        self.console.print("[bold]Welcome to RAG Terminal![/bold]")
        self.console.print("[dim]Type your query and press Enter to search.[/dim]")
        self.console.print("[dim]Commands:[/dim]")
        self.console.print("  [cyan]/help[/cyan] - Show help")
        self.console.print("  [cyan]/clear[/cyan] - Clear chat")
        self.console.print("  [cyan]/quit[/cyan] - Exit")
        self.console.print()

    async def run(self):
        """Main run loop."""
        self.print_welcome()

        while True:
            user_input = self.input_prompt.get_input()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/quit", "/exit", "/q"]:
                self.console.print("[yellow]Goodbye![/yellow]")
                break

            if user_input.lower() == "/clear":
                self.chat_history = []
                self.render()
                continue

            if user_input.lower() == "/help":
                self.console.print("[cyan]Available commands:[/cyan]")
                self.console.print("  /help - Show this help")
                self.console.print("  /clear - Clear chat history")
                self.console.print("  /quit - Exit terminal")
                continue

            # Process query
            self.console.print(create_thinking_bubble())

            try:
                result = await self.pipeline.process_query(user_input)

                # Add to history
                self.chat_history.append((
                    "user",
                    user_input,
                    [],
                    0
                ))
                self.chat_history.append((
                    "assistant",
                    result.response,
                    result.sources,
                    result.latency_ms
                ))

            except Exception as e:
                self.console.print(create_error_bubble(str(e)))

            # Re-render
            self.render()

def main():
    """Entry point."""
    # This would connect to actual pipeline
    # For now, show how it would be structured

    async def run_demo():
        """Demo mode without actual pipeline."""
        console = ConsoleManager().console
        console.print("[bold green]RAG Terminal initialized[/bold green]")
        console.print("[dim]Demo mode - connect to pipeline for full functionality[/dim]")

    asyncio.run(run_demo())

if __name__ == "__main__":
    main()
```

## Usage

```bash
# Run terminal UI
python -m ui_terminal

# With full pipeline
python -m ui_terminal --pipeline full

# Demo mode
python -m ui_terminal --demo
```

## Example Output

```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 RAG Terminal                                              │
│ Retrieval-Augmented Generation System                        │
│ Layers: Ingestion → Query → Rank → Synthesize               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  What is machine learning?                                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Machine learning is a subset of artificial intelligence
│  that enables systems to learn from data without being
│  explicitly programmed.
│
│  [Latency: 1250ms]
│
│  [SOURCES]
│  1. ml_intro.pdf [0.95]
│  2. ai_overview.pdf [0.87]
│  3. neural_networks.pdf [0.82]                               │
└──────────────────────────────────────────────────────────────┘

Session: default | Documents: 150 | Latency: 1250ms

❯ _
```

## Color Themes

```python
# ui_terminal/console/themes.py
from rich.theme import Theme

DARK_THEME = Theme({
    "primary": "cyan",
    "secondary": "blue",
    "accent": "magenta",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "user": "bold cyan",
    "assistant": "white",
    "source": "dim",
    "header": "bold magenta",
    "muted": "dim",
})

LIGHT_THEME = Theme({
    "primary": "blue",
    "secondary": "cyan",
    "accent": "magenta",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "user": "bold blue",
    "assistant": "black",
    "source": "dim",
    "header": "bold magenta",
    "muted": "dim",
})

HACKER_THEME = Theme({
    "primary": "green",
    "secondary": "cyan",
    "accent": "green bold",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "user": "bold green",
    "assistant": "green",
    "source": "green dim",
    "header": "bold green",
    "muted": "green dim",
})
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Submit query |
| Ctrl+C | Cancel current query |
| Ctrl+L | Clear screen |
| Up/Down | Navigate history |

---

**Previous**: [Layer 4: Synthesis & Memory](./layer-4-synthesis-memory.md)
