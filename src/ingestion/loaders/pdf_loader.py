"""PDF Loader — dùng PyMuPDF để extract text từ báo cáo marketing."""
from pathlib import Path
import json
import re


class PDFLoader:
    """Load PDF với PyMuPDF, extract metadata chiến dịch."""

    def load(self, file_path: Path) -> list[str]:
        """Trả về list text theo từng trang."""
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return pages

    def load_with_metadata(self, file_path: Path) -> list[dict]:
        """Load PDF kèm metadata campaign từ tên file."""
        import fitz

        # Extract report_month từ tên file (bao_cao_marketing_2023-03.pdf)
        report_month = ""
        match = re.search(r"(\d{4}-\d{2})", file_path.name)
        if match:
            report_month = match.group(1)

        doc = fitz.open(str(file_path))
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()

        if not full_text.strip():
            return []

        metadata = {
            "source_file": file_path.name,
            "report_month": report_month,
            "doc_type": "campaign_report",
        }

        return [{
            "text": full_text,
            "metadata": json.dumps(metadata, ensure_ascii=False),
            "raw": metadata,
        }]
