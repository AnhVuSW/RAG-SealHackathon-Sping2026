from typing import Iterator
import re


class SemanticChunker:
    """Split text by semantic boundaries (sentences, paragraphs)."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        split_by: str = "sentence",
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.split_by = split_by

    def chunk(self, text: str, metadata: dict = None) -> Iterator[dict]:
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
                overlap_text = current_chunk[-1]
                current_chunk = [overlap_text] if self.overlap > 0 else []
                current_size = len(overlap_text) if self.overlap > 0 else 0

            current_chunk.append(unit)
            current_size += unit_size

        if current_chunk:
            yield self._create_chunk(current_chunk, metadata)

    def _split_sentences(self, text: str) -> list[str]:
        pattern = r'(?<=[。！？.!?])\s+'
        return re.split(pattern, text)

    def _split_paragraphs(self, text: str) -> list[str]:
        return [p.strip() for p in text.split("\n\n") if p.strip()]

    def _create_chunk(self, units: list[str], metadata: dict) -> dict:
        return {
            "text": "".join(units),
            "metadata": metadata or {},
        }
