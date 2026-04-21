from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator


class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> list[str]:
        """Load and extract text from a file."""
        pass

    @abstractmethod
    def load_pages(self, file_path: Path) -> list[tuple[int, str]]:
        """Load file page by page with page numbers."""
        pass


class LoadResult:
    """Result of a load operation."""

    def __init__(self, texts: list[str], metadata: dict):
        self.texts = texts
        self.metadata = metadata
