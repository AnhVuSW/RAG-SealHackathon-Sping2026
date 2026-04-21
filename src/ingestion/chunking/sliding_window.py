from typing import Iterator


class SlidingWindowChunker:
    """Sliding window chunking strategy."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> Iterator[dict]:
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            yield {
                "text": text[start:end],
                "metadata": metadata or {},
            }
            start += self.chunk_size - self.overlap
