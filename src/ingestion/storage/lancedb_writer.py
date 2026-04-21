"""LanceDB writer & reader — hỗ trợ multiple collections."""
import lancedb
import pyarrow as pa
import numpy as np
from pathlib import Path


EMBEDDING_DIM = 1024  # bge-m3


def _make_schema(dim: int = EMBEDDING_DIM) -> pa.Schema:
    return pa.schema([
        pa.field("id", pa.string()),
        pa.field("text", pa.string()),
        pa.field("metadata", pa.string()),
        pa.field("embedding", pa.list_(pa.float32(), dim)),
    ])


class LanceDBWriter:
    """Write/read documents vào LanceDB, support nhiều table."""

    def __init__(self, uri: str, table_name: str = "documents"):
        self.uri = uri
        self.table_name = table_name
        Path(uri).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(uri)

    # ── Write ──────────────────────────────────────────────

    def ensure_table(self, overwrite: bool = False):
        """Tạo hoặc mở table."""
        schema = _make_schema()
        if self.table_name in self.db.table_names():
            if overwrite:
                self.db.drop_table(self.table_name)
            else:
                return self.db.open_table(self.table_name)
        return self.db.create_table(self.table_name, schema=schema)

    def write(self, chunks: list[dict], overwrite: bool = False):
        """Ghi chunks vào table. chunk phải có keys: id, text, metadata, embedding."""
        if not chunks:
            return
        table = self.ensure_table(overwrite=overwrite)
        table.add(chunks)

    def write_batch(self, chunks: list[dict], batch_size: int = 100, overwrite: bool = False):
        if not chunks:
            return
        table = self.ensure_table(overwrite=overwrite)
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i + batch_size]
            table.add(batch)
            print(f"  Written {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    # ── Search ─────────────────────────────────────────────

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[dict]:
        """Vector search trong table hiện tại."""
        if self.table_name not in self.db.table_names():
            return []
        table = self.db.open_table(self.table_name)
        results = (
            table.search(query_embedding)
            .limit(top_k)
            .to_list()
        )
        docs = []
        for r in results:
            docs.append({
                "id": r.get("id", ""),
                "text": r.get("text", ""),
                "metadata": r.get("metadata", "{}"),
                "relevance_score": float(r.get("_distance", 0.0)),
            })
        return docs

    def count(self) -> int:
        if self.table_name not in self.db.table_names():
            return 0
        return self.db.open_table(self.table_name).count_rows()
