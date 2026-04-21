"""CSV Loader — đọc 35 file feedback CSV từ phan_hoi_hang_thang/"""
from pathlib import Path
import pandas as pd
import json


class CSVFeedbackLoader:
    """Load feedback CSV files → list of dicts (mỗi row = 1 document)."""

    def load_dir(self, folder: Path) -> list[dict]:
        """Concat tất cả CSV trong folder, trả về list record."""
        dfs = []
        for f in sorted(folder.glob("*.csv")):
            try:
                df = pd.read_csv(f, encoding="utf-8")
                dfs.append(df)
            except Exception as e:
                print(f"  [CSV] Skip {f.name}: {e}")

        if not dfs:
            return []

        combined = pd.concat(dfs, ignore_index=True)
        # Đảm bảo cột created_at là string để dễ filter sau
        if "created_at" in combined.columns:
            combined["created_at"] = combined["created_at"].astype(str)

        records = []
        for _, row in combined.iterrows():
            row_dict = row.to_dict()
            # text dùng để embed
            feedback_text = str(row_dict.get("feedback_text", ""))
            records.append({
                "text": feedback_text,
                "metadata": json.dumps(row_dict, ensure_ascii=False, default=str),
                "raw": row_dict,
            })
        return records

    def load_dataframe(self, folder: Path) -> pd.DataFrame:
        """Trả về DataFrame gộp tất cả CSV — dùng cho pandas tool."""
        dfs = []
        for f in sorted(folder.glob("*.csv")):
            try:
                df = pd.read_csv(f, encoding="utf-8")
                dfs.append(df)
            except Exception:
                pass
        if not dfs:
            return pd.DataFrame()
        combined = pd.concat(dfs, ignore_index=True)
        if "created_at" in combined.columns:
            combined["created_at"] = pd.to_datetime(
                combined["created_at"], errors="coerce"
            )
        return combined
