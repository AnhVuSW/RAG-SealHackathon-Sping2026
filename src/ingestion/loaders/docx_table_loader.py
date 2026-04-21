"""DOCX Table Loader — parse bảng voucher từ the_le_voucher_300_ma.docx"""
from pathlib import Path
import json
import re


class DocxTableLoader:
    """Parse bảng có cấu trúc từ DOCX → list of dicts."""

    def load(self, file_path: Path) -> list[dict]:
        from docx import Document

        doc = Document(file_path)
        records = []

        for table in doc.tables:
            if len(table.rows) < 2:
                continue

            # Lấy header từ row đầu tiên
            headers = []
            for cell in table.rows[0].cells:
                headers.append(cell.text.strip())

            # Parse từng row data
            for row in table.rows[1:]:
                values = [cell.text.strip() for cell in row.cells]
                if not any(values):  # bỏ row trống
                    continue

                record = {}
                for i, header in enumerate(headers):
                    val = values[i] if i < len(values) else ""
                    record[header] = val

                # Map image_path theo voucher_code
                voucher_code = record.get("voucher_code", record.get("Mã voucher", ""))
                record["image_path"] = self._map_image_path(voucher_code)

                # text để embed: tóm tắt thông tin voucher
                record["text"] = self._build_text(record)
                record["metadata"] = json.dumps(record, ensure_ascii=False, default=str)
                records.append(record)

        return records

    def _map_image_path(self, voucher_code: str) -> str:
        """Map voucher code → tên file ảnh (e.g., VCH00001 → the_voucher_0001_VCH00001.jpg)."""
        if not voucher_code:
            return ""
        # Extract số từ code
        nums = re.findall(r"\d+", voucher_code)
        if nums:
            num = nums[0].zfill(4)
            return f"the_voucher_{num}_{voucher_code}.jpg"
        return ""

    def _build_text(self, record: dict) -> str:
        """Tạo text mô tả voucher để embed."""
        parts = []
        for key, val in record.items():
            if key not in ("text", "metadata", "image_path") and val:
                parts.append(f"{key}: {val}")
        return " | ".join(parts)

    def load_dataframe(self, file_path: Path):
        """Trả về DataFrame vouchers — dùng cho voucher tool."""
        import pandas as pd
        records = self.load(file_path)
        if not records:
            return pd.DataFrame()
        # Loại bỏ các key nội bộ để clean DataFrame
        clean = []
        for r in records:
            row = {k: v for k, v in r.items() if k not in ("text", "metadata")}
            clean.append(row)
        return pd.DataFrame(clean)
