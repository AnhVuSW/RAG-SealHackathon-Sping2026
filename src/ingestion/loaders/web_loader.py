import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Iterator
from .base_loader import BaseLoader


class WebLoader(BaseLoader):
    """Load content from web pages."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def load(self, file_path: Path) -> list[str]:
        url = str(file_path)
        response = requests.get(url, timeout=self.timeout)
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return [soup.get_text(separator="\n", strip=True)]

    def load_pages(self, file_path: Path) -> list[tuple[int, str]]:
        content = self.load(file_path)
        return [(1, content[0])]

    def load_many(self, urls: list[str]) -> Iterator[tuple[str, str]]:
        for url in urls:
            try:
                content = self.load(Path(url))
                yield url, content[0]
            except Exception as e:
                print(f"Failed to load {url}: {e}")
                continue
