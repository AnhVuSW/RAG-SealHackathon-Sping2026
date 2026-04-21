"""Marketing Data Ingestion Pipeline — Layer 1."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import uuid
import json

from .config import IngestionConfig
from .loaders import CSVFeedbackLoader, DocxTableLoader, PDFLoader, HTMLEmailLoader, DocxLoader
from .chunking import SemanticChunker
from .storage import LanceDBWriter


@dataclass
class IngestResult:
    total_chunks: int
    total_docs: int
    collections: dict  # {table_name: count}


class MarketingIngestionPipeline:
    """
    Ingest marketing data vào LanceDB theo thứ tự ưu tiên:
      ESSENTIAL: feedbacks (CSV), vouchers (DOCX table), campaigns (PDF)
      USEFUL:    campaigns (HTML email), policies (DOCX)
    """

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        self.chunker = SemanticChunker(
            chunk_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap,
        )

    def ingest(self, data_root: str) -> IngestResult:
        """Main entry point — ingest toàn bộ marketing data."""
        from .embedding import BGEEmbeddings

        root = Path(data_root)
        marketing_dir = root / "MARKETING"

        from src.config import POLICY_DATA_PATH
        policy_dir = POLICY_DATA_PATH

        embeddings = BGEEmbeddings(
            model_name=self.config.embedding_model,
            device=self.config.embedding_device,
        )

        collections = {}
        total_chunks = 0
        total_docs = 0

        # ── 1. FEEDBACKS (CSV) ─────────────────────────────
        print("\n[1/5] Ingesting Feedbacks (CSV)...")
        feedback_dir = marketing_dir / "phan_hoi_hang_thang"
        if feedback_dir.exists():
            n_chunks, n_docs = self._ingest_feedbacks(feedback_dir, embeddings)
            collections["feedbacks"] = n_chunks
            total_chunks += n_chunks
            total_docs += n_docs
            print(f"  ✓ feedbacks: {n_chunks} chunks from {n_docs} files")
        else:
            print(f"  ⚠ Not found: {feedback_dir}")

        # ── 2. VOUCHERS (DOCX table) ───────────────────────
        print("\n[2/5] Ingesting Vouchers (DOCX table)...")
        voucher_file = marketing_dir / "the_le_voucher_300_ma.docx"
        if voucher_file.exists():
            n_chunks, n_docs = self._ingest_vouchers(voucher_file, embeddings)
            collections["vouchers"] = n_chunks
            total_chunks += n_chunks
            total_docs += n_docs
            print(f"  ✓ vouchers: {n_chunks} records")
        else:
            print(f"  ⚠ Not found: {voucher_file}")

        # ── 3. CAMPAIGNS (PDF reports) ─────────────────────
        print("\n[3/5] Ingesting Campaigns (PDF)...")
        pdf_dir = marketing_dir / "bao_cao_marketing"
        if pdf_dir.exists():
            n_chunks, n_docs = self._ingest_campaigns_pdf(pdf_dir, embeddings)
            collections["campaigns"] = n_chunks
            total_chunks += n_chunks
            total_docs += n_docs
            print(f"  ✓ campaigns (PDF): {n_chunks} chunks from {n_docs} files")
        else:
            print(f"  ⚠ Not found: {pdf_dir}")

        # ── 4. CAMPAIGNS (HTML email) ──────────────────────
        print("\n[4/5] Ingesting Email Marketing (HTML)...")
        html_dir = marketing_dir / "email_marketing"
        if html_dir.exists():
            n_chunks, n_docs = self._ingest_campaigns_html(html_dir, embeddings)
            collections["campaigns"] = collections.get("campaigns", 0) + n_chunks
            total_chunks += n_chunks
            total_docs += n_docs
            print(f"  ✓ campaigns (HTML): {n_chunks} chunks from {n_docs} files")
        else:
            print(f"  ⚠ Not found: {html_dir}")

        # ── 5. POLICIES (DOCX) ────────────────────────────
        print("\n[5/5] Ingesting Company Policies (DOCX)...")
        if policy_dir.exists():
            n_chunks, n_docs = self._ingest_policies(policy_dir, embeddings)
            collections["policies"] = n_chunks
            total_chunks += n_chunks
            total_docs += n_docs
            print(f"  ✓ policies: {n_chunks} chunks from {n_docs} files")
        else:
            print(f"  ⚠ Not found: {policy_dir}")

        print(f"\n✅ Ingestion complete: {total_chunks} total chunks, {total_docs} documents")
        return IngestResult(
            total_chunks=total_chunks,
            total_docs=total_docs,
            collections=collections,
        )

    # ── Private helpers ────────────────────────────────────

    def _ingest_feedbacks(self, folder: Path, embeddings) -> tuple[int, int]:
        loader = CSVFeedbackLoader()
        records = loader.load_dir(folder)
        if not records:
            return 0, 0

        writer = LanceDBWriter(uri=self.config.lancedb_uri, table_name="feedbacks")
        chunks = []
        for i, r in enumerate(records):
            text = r["text"]
            if not text.strip():
                continue
            emb = embeddings.embed([text])[0]
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": r["metadata"],
                "embedding": emb,
            })

        writer.write(chunks, overwrite=True)
        return len(chunks), len(list(folder.glob("*.csv")))

    def _ingest_vouchers(self, file_path: Path, embeddings) -> tuple[int, int]:
        loader = DocxTableLoader()
        records = loader.load(file_path)
        if not records:
            return 0, 0

        writer = LanceDBWriter(uri=self.config.lancedb_uri, table_name="vouchers")
        chunks = []
        for r in records:
            text = r.get("text", "")
            if not text.strip():
                continue
            emb = embeddings.embed([text])[0]
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": r.get("metadata", "{}"),
                "embedding": emb,
            })

        writer.write(chunks, overwrite=True)
        return len(chunks), 1

    def _ingest_campaigns_pdf(self, folder: Path, embeddings) -> tuple[int, int]:
        loader = PDFLoader()
        writer = LanceDBWriter(uri=self.config.lancedb_uri, table_name="campaigns")
        chunks = []
        n_docs = 0

        for pdf_file in sorted(folder.glob("*.pdf")):
            try:
                records = loader.load_with_metadata(pdf_file)
                for r in records:
                    # Chunk text dài
                    sub_chunks = self.chunker.chunk(r["text"], {
                        "source": pdf_file.name,
                        **json.loads(r.get("metadata", "{}")),
                    })
                    for sc in sub_chunks:
                        emb = embeddings.embed([sc["text"]])[0]
                        chunks.append({
                            "id": str(uuid.uuid4()),
                            "text": sc["text"],
                            "metadata": json.dumps(sc.get("metadata", {}), ensure_ascii=False),
                            "embedding": emb,
                        })
                n_docs += 1
            except Exception as e:
                print(f"  [PDF] Skip {pdf_file.name}: {e}")

        writer.write(chunks, overwrite=True)
        return len(chunks), n_docs

    def _ingest_campaigns_html(self, folder: Path, embeddings) -> tuple[int, int]:
        loader = HTMLEmailLoader()
        records = loader.load_dir(folder)
        writer = LanceDBWriter(uri=self.config.lancedb_uri, table_name="campaigns")
        chunks = []

        for r in records:
            text = r.get("text", "")
            if not text.strip():
                continue
            emb = embeddings.embed([text])[0]
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": r.get("metadata", "{}"),
                "embedding": emb,
            })

        if chunks:
            # Append vào campaigns table (không overwrite — PDF đã ghi rồi)
            writer_append = LanceDBWriter(uri=self.config.lancedb_uri, table_name="campaigns")
            writer_append.write(chunks, overwrite=False)

        return len(chunks), len(list(folder.glob("*.html")))

    def _ingest_policies(self, folder: Path, embeddings) -> tuple[int, int]:
        loader = DocxLoader()
        writer = LanceDBWriter(uri=self.config.lancedb_uri, table_name="policies")
        chunks = []
        n_docs = 0

        for docx_file in sorted(folder.glob("*.docx")):
            try:
                texts = loader.load(docx_file)
                for text in texts:
                    sub_chunks = self.chunker.chunk(text, {
                        "source": docx_file.name,
                        "doc_type": "policy",
                        "policy_name": docx_file.stem,
                    })
                    for sc in sub_chunks:
                        emb = embeddings.embed([sc["text"]])[0]
                        chunks.append({
                            "id": str(uuid.uuid4()),
                            "text": sc["text"],
                            "metadata": json.dumps(sc.get("metadata", {}), ensure_ascii=False),
                            "embedding": emb,
                        })
                n_docs += 1
            except Exception as e:
                print(f"  [Policy] Skip {docx_file.name}: {e}")

        writer.write(chunks, overwrite=True)
        return len(chunks), n_docs


# Backward-compatible alias
class DocumentIngestionPipeline(MarketingIngestionPipeline):
    pass
