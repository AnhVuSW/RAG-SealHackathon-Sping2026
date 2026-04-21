"""HTML Loader — parse email marketing HTML files từ email_marketing/"""
from pathlib import Path
import json
import re


class HTMLEmailLoader:
    """Load HTML email files → list of dicts với KPI metadata."""

    def load_dir(self, folder: Path) -> list[dict]:
        records = []
        for f in sorted(folder.glob("*.html")):
            try:
                record = self._parse_email(f)
                if record:
                    records.append(record)
            except Exception as e:
                print(f"  [HTML] Skip {f.name}: {e}")
        return records

    def _parse_email(self, file_path: Path) -> dict:
        from bs4 import BeautifulSoup

        html = file_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        # Extract text content
        text = soup.get_text(separator=" ", strip=True)

        # Extract campaign ID từ filename (email_001_CAM0001.html)
        campaign_id = ""
        match = re.search(r"(CAM\d+)", file_path.name)
        if match:
            campaign_id = match.group(1)

        # Extract voucher codes nhúng trong email
        voucher_codes = re.findall(r"VCH\d+", text)

        # Extract KPI numbers từ text (heuristic)
        metadata = {
            "campaign_id": campaign_id,
            "source_file": file_path.name,
            "doc_type": "email",
            "voucher_codes": ",".join(voucher_codes),
        }

        return {
            "text": text[:2000],  # Giới hạn độ dài
            "metadata": json.dumps(metadata, ensure_ascii=False),
            "raw": metadata,
        }
